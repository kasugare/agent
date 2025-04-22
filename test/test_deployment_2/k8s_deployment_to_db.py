import yaml
import mysql.connector
from mysql.connector import Error
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class K8sDeploymentManager:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        try:
            self.conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor(dictionary=True)
            self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            logger.info("Database connection established")
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def generate_id(self, prefix: str, sequence: int) -> str:
        """고유 ID 생성"""
        id = "%s_%X_%04d" %(prefix, int(time.time()*100000), sequence)
        return id

    def insert_deployment(self, yaml_data: Dict[str, Any]) -> str:
        """Deployment 전체 데이터 저장"""
        try:
            # 1. Application 등록
            app_id = self.insert_application(yaml_data)

            # 2. Deployment 기본 정보 등록
            deployment_id = self.insert_deployment_base(app_id, yaml_data)

            # 3. 메타데이터 등록
            self.insert_metadata(deployment_id, yaml_data['metadata'])

            # 4. Spec 등록
            self.insert_spec(deployment_id, yaml_data['spec'])

            self.conn.commit()
            logger.info(f"Successfully inserted deployment: {deployment_id}")
            return deployment_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting deployment: {e}")
            raise

    def insert_application(self, yaml_data: Dict[str, Any]) -> str:
        """애플리케이션 정보 저장"""
        app_id = self.generate_id("APP", 1)
        query = """
		INSERT INTO k8s_applications (
			app_id, app_name, app_namespace, app_description
		) VALUES (%s, %s, %s, %s)
		"""
        self.cursor.execute(query, (
            app_id,
            yaml_data['metadata']['name'],
            yaml_data['metadata']['namespace'],
            yaml_data['metadata'].get('annotations', {}).get('description', '')
        ))
        return app_id

    def insert_deployment_base(self, app_id: str, yaml_data: Dict[str, Any]) -> str:
        """Deployment 기본 정보 저장"""
        deployment_id = self.generate_id("DEP", 1)
        spec = yaml_data['spec']

        query = """
		INSERT INTO k8s_deployments (
			deployment_id, app_id, deployment_name, deployment_namespace,
			replica_count, service_account_name, automount_service_account_token,
			host_network, dns_policy, priority_class_name, restart_policy,
			termination_grace_period_seconds
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""

        template_spec = spec['template']['spec']
        self.cursor.execute(query, (
            deployment_id,
            app_id,
            yaml_data['metadata']['name'],
            yaml_data['metadata']['namespace'],
            spec['replicas'],
            template_spec.get('serviceAccountName'),
            template_spec.get('automountServiceAccountToken', True),
            template_spec.get('hostNetwork', False),
            template_spec.get('dnsPolicy', 'ClusterFirst'),
            template_spec.get('priorityClassName'),
            template_spec.get('restartPolicy', 'Always'),
            template_spec.get('terminationGracePeriodSeconds', 30)
        ))
        return deployment_id

    def insert_metadata(self, deployment_id: str, metadata: Dict[str, Any]) -> None:
        """메타데이터(레이블, 어노테이션) 저장"""
        # Labels
        for key, value in metadata.get('labels', {}).items():
            label_id = self.generate_id("LBL", 1)
            query = """
			INSERT INTO k8s_deployment_labels (
				label_id, deployment_id, label_key, label_value
			) VALUES (%s, %s, %s, %s)
			"""
            self.cursor.execute(query, (label_id, deployment_id, key, value))

        # Annotations
        for key, value in metadata.get('annotations', {}).items():
            annotation_id = self.generate_id("ANN", 1)
            query = """
			INSERT INTO k8s_deployment_annotations (
				annotation_id, deployment_id, annotation_key, annotation_value
			) VALUES (%s, %s, %s, %s)
			"""
            self.cursor.execute(query, (annotation_id, deployment_id, key, value))

    def insert_spec(self, deployment_id: str, spec: Dict[str, Any]) -> None:
        """Deployment Spec 저장"""
        # 1. Selector 저장
        self.insert_selector(deployment_id, spec['selector'])

        # 2. Template 저장
        template_id = self.insert_template(deployment_id, spec['template'])

        # 3. Pod Spec 저장
        self.insert_pod_spec(template_id, spec['template']['spec'])

    def insert_selector(self, deployment_id: str, selector: Dict[str, Any]) -> None:
        """Selector 저장"""
        for key, value in selector.get('matchLabels', {}).items():
            selector_id = self.generate_id("SEL", 1)
            query = """
			INSERT INTO k8s_deployment_selectors (
				selector_id, deployment_id, label_key, label_value
			) VALUES (%s, %s, %s, %s)
			"""
            self.cursor.execute(query, (selector_id, deployment_id, key, value))

    def insert_template(self, deployment_id: str, template: Dict[str, Any]) -> str:
        """Pod Template 저장"""
        template_id = self.generate_id("TPL", 1)
        query = """
		INSERT INTO k8s_pod_templates (template_id, deployment_id)
		VALUES (%s, %s)
		"""
        self.cursor.execute(query, (template_id, deployment_id))

        # Template Labels 저장
        for key, value in template['metadata'].get('labels', {}).items():
            label_id = self.generate_id("TLBL", 1)
            query = """
			INSERT INTO k8s_pod_template_labels (
				label_id, template_id, label_key, label_value
			) VALUES (%s, %s, %s, %s)
			"""
            self.cursor.execute(query, (label_id, template_id, key, value))

        return template_id


    def insert_pod_spec(self, template_id: str, pod_spec: Dict[str, Any]) -> None:
        """Pod Spec 저장"""
        # hostNetwork 설정 업데이트
        if 'hostNetwork' in pod_spec:
            query = """
               UPDATE k8s_pod_templates 
               SET host_network = %s 
               WHERE template_id = %s
               """
            self.cursor.execute(query, (pod_spec['hostNetwork'], template_id))

        # nodeSelector 저장
        if 'nodeSelector' in pod_spec:
            for key, value in pod_spec['nodeSelector'].items():
                selector_id = self.generate_id("NS", 1)
                query = """
                   INSERT INTO k8s_node_selectors (
                       selector_id, template_id, label_key, label_value
                   ) VALUES (%s, %s, %s, %s)
                   """
                self.cursor.execute(query, (selector_id, template_id, key, value))

        """Pod Spec 저장"""
        # 1. Affinity 저장
        if 'affinity' in pod_spec:
            self.insert_affinity(template_id, pod_spec['affinity'])

        # 2. Containers 저장
        for container in pod_spec['containers']:
            self.insert_container(template_id, container)

        # 3. Volumes 저장
        if 'volumes' in pod_spec:
            self.insert_volumes(template_id, pod_spec['volumes'])

        # 4. DNS Config 저장
        if 'dnsConfig' in pod_spec:
            self.insert_dns_config(template_id, pod_spec['dnsConfig'])

        # 5. Host Aliases 저장
        if 'hostAliases' in pod_spec:
            self.insert_host_aliases(template_id, pod_spec['hostAliases'])

        # 6. Topology Spread Constraints 저장
        if 'topologySpreadConstraints' in pod_spec:
            self.insert_topology_spread_constraints(
                template_id,
                pod_spec['topologySpreadConstraints']
            )


    def insert_affinity(self, template_id: str, affinity: Dict[str, Any]) -> None:
        """Affinity 설정 저장"""
        # Node Affinity
        if 'nodeAffinity' in affinity:
            self.insert_node_affinity(template_id, affinity['nodeAffinity'])

        # Pod Affinity
        if 'podAffinity' in affinity:
            self.insert_pod_affinity(template_id, affinity['podAffinity'], 'podAffinity')

        # Pod Anti-Affinity
        if 'podAntiAffinity' in affinity:
            self.insert_pod_affinity(template_id, affinity['podAntiAffinity'], 'podAntiAffinity')

    def insert_node_affinity(self, template_id: str, node_affinity: Dict[str, Any]) -> None:
        """Node Affinity 저장"""
        # Required Rules
        if 'requiredDuringSchedulingIgnoredDuringExecution' in node_affinity:
            rule_id = self.generate_id("NAR", 1)
            query = """
			INSERT INTO k8s_node_affinity_rules (
				rule_id, template_id, rule_type
			) VALUES (%s, %s, %s)
			"""
            self.cursor.execute(query, (rule_id, template_id, 'required'))

            required = node_affinity['requiredDuringSchedulingIgnoredDuringExecution']
            self.insert_node_selector_terms(rule_id, required.get('nodeSelectorTerms', []))

        # Preferred Rules
        if 'preferredDuringSchedulingIgnoredDuringExecution' in node_affinity:
            preferred = node_affinity['preferredDuringSchedulingIgnoredDuringExecution']
            for idx, preference in enumerate(preferred, 1):
                rule_id = self.generate_id("NAR", idx + 100)
                query = """
				INSERT INTO k8s_node_affinity_rules (
					rule_id, template_id, rule_type, weight
				) VALUES (%s, %s, %s, %s)
				"""
                self.cursor.execute(query, (
                    rule_id, template_id, 'preferred', preference['weight']
                ))

                self.insert_node_selector_terms(
                    rule_id,
                    [preference['preference']]
                )

    def insert_node_selector_terms(self, rule_id: str, terms: List[Dict[str, Any]]) -> None:
        """Node Selector Terms 저장"""
        for term_idx, term in enumerate(terms, 1):
            term_id = self.generate_id("NST", term_idx)
            query = """
			INSERT INTO k8s_node_selector_terms (
				term_id, rule_id, term_order
			) VALUES (%s, %s, %s)
			"""
            self.cursor.execute(query, (term_id, rule_id, term_idx))

            if 'matchExpressions' in term:
                self.insert_node_match_expressions(
                    term_id,
                    term['matchExpressions']
                )

    def insert_node_match_expressions(
            self,
            term_id: str,
            expressions: List[Dict[str, Any]]
    ) -> None:
        """Node Match Expressions 저장"""
        for expr_idx, expr in enumerate(expressions, 1):
            expr_id = self.generate_id("NME", expr_idx)
            query = """
			INSERT INTO k8s_node_match_expressions (
				expression_id, term_id, label_key, operator, expression_order
			) VALUES (%s, %s, %s, %s, %s)
			"""
            self.cursor.execute(query, (
                expr_id, term_id, expr['key'], expr['operator'], expr_idx
            ))

            if 'values' in expr:
                self.insert_node_match_expression_values(expr_id, expr['values'])

    def insert_node_match_expression_values(
            self,
            expression_id: str,
            values: List[str]
    ) -> None:
        """Node Match Expression Values 저장"""
        for val_idx, value in enumerate(values, 1):
            value_id = self.generate_id("NMEV", val_idx)
            query = """
			INSERT INTO k8s_node_match_expression_values (
				value_id, expression_id, label_value, value_order
			) VALUES (%s, %s, %s, %s)
			"""
            self.cursor.execute(query, (value_id, expression_id, value, val_idx))

    def insert_pod_affinity(
            self,
            template_id: str,
            pod_affinity: Dict[str, Any],
            affinity_type: str
    ) -> None:
        """Pod Affinity/Anti-Affinity 저장"""
        # Required Rules
        if 'requiredDuringSchedulingIgnoredDuringExecution' in pod_affinity:
            required = pod_affinity['requiredDuringSchedulingIgnoredDuringExecution']
            for idx, term in enumerate(required, 1):
                rule_id = self.generate_id("PAR", idx)
                self.insert_pod_affinity_rule(
                    template_id, rule_id, affinity_type,
                    'required', None, term
                )

        # Preferred Rules
        if 'preferredDuringSchedulingIgnoredDuringExecution' in pod_affinity:
            preferred = pod_affinity['preferredDuringSchedulingIgnoredDuringExecution']
            for idx, pref in enumerate(preferred, 1):
                rule_id = self.generate_id("PAR", idx + 100)
                self.insert_pod_affinity_rule(
                    template_id, rule_id, affinity_type,
                    'preferred', pref['weight'], pref['podAffinityTerm']
                )

    def insert_pod_affinity_rule(
            self,
            template_id: str,
            rule_id: str,
            affinity_type: str,
            rule_type: str,
            weight: int,
            term: Dict[str, Any]
    ) -> None:
        """Pod Affinity Rule 저장"""
        query = """
		INSERT INTO k8s_pod_affinity_rules (
			rule_id, template_id, affinity_type, rule_type, 
			weight, topology_key
		) VALUES (%s, %s, %s, %s, %s, %s)
		"""
        self.cursor.execute(query, (
            rule_id, template_id, affinity_type, rule_type,
            weight, term['topologyKey']
        ))

        if 'labelSelector' in term:
            self.insert_pod_label_selector(rule_id, term['labelSelector'])

        if 'namespaceSelector' in term:
            self.insert_namespace_selector(rule_id, term['namespaceSelector'])

    def insert_pod_label_selector(
            self,
            rule_id: str,
            label_selector: Dict[str, Any]
    ) -> None:
        """Pod Label Selector 저장"""
        selector_id = self.generate_id("PLS", 1)
        query = """
		INSERT INTO k8s_pod_label_selectors (
			selector_id, rule_id
		) VALUES (%s, %s)
		"""
        self.cursor.execute(query, (selector_id, rule_id))

        if 'matchExpressions' in label_selector:
            for idx, expr in enumerate(label_selector['matchExpressions'], 1):
                expr_id = self.generate_id("PME", idx)
                query = """
				INSERT INTO k8s_pod_match_expressions (
					expression_id, selector_id, label_key,
					operator, expression_order
				) VALUES (%s, %s, %s, %s, %s)
				"""
                self.cursor.execute(query, (
                    expr_id, selector_id, expr['key'],
                    expr['operator'], idx
                ))

                if 'values' in expr:
                    for val_idx, value in enumerate(expr['values'], 1):
                        value_id = self.generate_id("PMEV", val_idx)
                        query = """
						INSERT INTO k8s_pod_match_expression_values (
							value_id, expression_id, label_value, value_order
						) VALUES (%s, %s, %s, %s)
						"""
                        self.cursor.execute(query, (
                            value_id, expr_id, value, val_idx
                        ))

    def insert_namespace_selector(self, rule_id: str, namespace_selector: Dict[str, Any]) -> None:
        """Namespace Selector 저장"""
        selector_id = self.generate_id("NS", 1)
        query = """
		INSERT INTO k8s_namespace_selectors (
			selector_id, rule_id
		) VALUES (%s, %s)
		"""
        self.cursor.execute(query, (selector_id, rule_id))

        if 'matchLabels' in namespace_selector:
            for key, value in namespace_selector['matchLabels'].items():
                label_id = self.generate_id("NSL", 1)
                query = """
				INSERT INTO k8s_namespace_match_labels (
					label_id, selector_id, label_key, label_value
				) VALUES (%s, %s, %s, %s)
				"""
                self.cursor.execute(query, (
                    label_id, selector_id, key, value
                ))

    def insert_container(self, template_id: str, container: Dict[str, Any]) -> None:
        """Container 정보 저장"""
        container_id = self.generate_id("CONT", 1)
        image_parts = container['image'].split(':')
        image_name = image_parts[0]
        image_tag = image_parts[1] if len(image_parts) > 1 else 'latest'

        query = """
		INSERT INTO k8s_containers (
			container_id, template_id, container_name,
			image_name, image_tag, image_pull_policy,
			working_dir, command, args
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
        self.cursor.execute(query, (
            container_id,
            template_id,
            container['name'],
            image_name,
            image_tag,
            container.get('imagePullPolicy', 'IfNotPresent'),
            container.get('workingDir'),
            json.dumps(container.get('command', [])),
            json.dumps(container.get('args', []))
        ))

        # Resources
        if 'resources' in container:
            self.insert_container_resources(container_id, container['resources'])

        # Ports
        if 'ports' in container:
            self.insert_container_ports(container_id, container['ports'])

        # Environment Variables
        if 'env' in container:
            self.insert_container_env_vars(container_id, container['env'])

        # Volume Mounts
        if 'volumeMounts' in container:
            self.insert_volume_mounts(container_id, container['volumeMounts'])

        # Probes
        self.insert_container_probes(container_id, container)

        # Lifecycle
        if 'lifecycle' in container:
            self.insert_lifecycle_hooks(container_id, container['lifecycle'])

        # Security Context
        if 'securityContext' in container:
            self.insert_security_context(container_id, container['securityContext'])

    # def insert_container_resources(
    #         self,
    #         container_id: str,
    #         resources: Dict[str, Any]
    # ) -> None:
    #     """Container Resources 저장"""
    #     for resource_type in ['requests', 'limits']:
    #         if resource_type in resources:
    #             for resource_name, value in resources[resource_type].items():
    #                 resource_id = self.generate_id("RES", 1)
    #                 query = """
	# 				INSERT INTO k8s_container_resources (
	# 					resource_id, container_id, resource_type,
	# 					resource_name, request_amount, limit_amount
	# 				) VALUES (%s, %s, %s, %s, %s, %s)
	# 				"""
    #                 self.cursor.execute(query, (
    #                     resource_id,
    #                     container_id,
    #                     'GPU' if 'gpu' in resource_name.lower() else resource_name.upper(),
    #                     resource_name,
    #                     value if resource_type == 'requests' else None,
    #                     value if resource_type == 'limits' else None
    #                 ))

    def insert_container_resources(self, container_id: str, resources: Dict[str, Any]) -> None:
        """컨테이너 리소스 설정 저장"""
        try:
            values = []
            resources_map = {}
            for res_type, res_info in resources.items():
                for key, value in res_info.items():
                    if key in resources_map.keys():
                        resources_map[key][res_type] = value
                    else:
                        resources_map[key] = {res_type: value}

            for resource_name, resource_info in resources_map.items():
                resource_id = self.generate_id("RES", len(values) + 1)
                resource_category = 'GPU' if 'gpu' in resource_name.lower() else resource_name.upper()
                values.append((
                    resource_id,
                    container_id,
                    resource_category,
                    resource_name,
                    resource_info.get('requests') if resource_info.get('requests') else None,
                    resource_info.get('limits') if resource_info.get('limits') else None
                ))

            if values:
                query = """
    				INSERT INTO k8s_container_resources (
    					resource_id, container_id, resource_type,
    					resource_name, request_amount, limit_amount
    				) VALUES (%s, %s, %s, %s, %s, %s)
    			"""
                self.cursor.executemany(query, values)
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting container resources: {e}")
            raise

    def insert_container_ports(
            self,
            container_id: str,
            ports: List[Dict[str, Any]]
    ) -> None:
        """Container Ports 저장"""
        for port in ports:
            port_id = self.generate_id("PORT", 1)
            query = """
			INSERT INTO k8s_container_ports (
				port_id, container_id, port_name,
				container_port, protocol
			) VALUES (%s, %s, %s, %s, %s)
			"""
            self.cursor.execute(query, (
                port_id,
                container_id,
                port.get('name'),
                port['containerPort'],
                port.get('protocol', 'TCP')
            ))

    def insert_container_env_vars(
            self,
            container_id: str,
            env_vars: List[Dict[str, Any]]
    ) -> None:
        """Container Environment Variables 저장"""
        for env in env_vars:
            env_id = self.generate_id("ENV", 1)

            if 'value' in env:
                value_type = 'PLAIN'
                value_reference = json.dumps({'value': env['value']})
            else:
                value_from = env['valueFrom']
                if 'fieldRef' in value_from:
                    value_type = 'FIELD_REF'
                    value_reference = json.dumps({'fieldPath': value_from['fieldRef']['fieldPath']})
                elif 'secretKeyRef' in value_from:
                    value_type = 'SECRET'
                    value_reference = json.dumps(value_from['secretKeyRef'])
                elif 'configMapKeyRef' in value_from:
                    value_type = 'CONFIG_MAP'
                    value_reference = json.dumps(value_from['configMapKeyRef'])

            query = """
			INSERT INTO k8s_env_variables (
				env_id, container_id, env_name,
				env_value_type, value_reference
			) VALUES (%s, %s, %s, %s, %s)
			"""
            self.cursor.execute(query, (
                env_id,
                container_id,
                env['name'],
                value_type,
                value_reference
            ))

    def insert_volume_mounts(
            self,
            container_id: str,
            mounts: List[Dict[str, Any]]
    ) -> None:
        """Volume Mounts 저장"""
        for mount in mounts:
            mount_id = self.generate_id("MOUNT", 1)
            query = """
			INSERT INTO k8s_volume_mounts (
				mount_id, container_id, volume_name,
				mount_path, sub_path, read_only
			) VALUES (%s, %s, %s, %s, %s, %s)
			"""
            self.cursor.execute(query, (
                mount_id,
                container_id,
                mount['name'],
                mount['mountPath'],
                mount.get('subPath'),
                mount.get('readOnly', False)
            ))

    def insert_container_probes(
            self,
            container_id: str,
            container: Dict[str, Any]
    ) -> None:
        """Container Probes 저장"""
        probe_types = ['livenessProbe', 'readinessProbe', 'startupProbe']

        for probe_type in probe_types:
            if probe_type in container:
                probe = container[probe_type]
                probe_id = self.generate_id("PROBE", 1)

                # Handler Type 결정
                handler_type = next(
                    (k for k in ['httpGet', 'tcpSocket', 'exec'] if k in probe),
                    None
                )
                if not handler_type:
                    continue

                handler_config = json.dumps(probe[handler_type])

                query = """
				INSERT INTO k8s_probes (
					probe_id, container_id, probe_type,
					handler_type, handler_config,
					initial_delay_seconds, period_seconds,
					timeout_seconds, success_threshold,
					failure_threshold
				) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
				"""
                self.cursor.execute(query, (
                    probe_id,
                    container_id,
                    probe_type.replace('Probe', ''),
                    handler_type,
                    handler_config,
                    probe.get('initialDelaySeconds'),
                    probe.get('periodSeconds'),
                    probe.get('timeoutSeconds'),
                    probe.get('successThreshold'),
                    probe.get('failureThreshold')
                ))

    def insert_lifecycle_hooks(self, container_id: str, lifecycle: Dict[str, Any]) -> None:
        """Lifecycle Hooks 저장"""
        for hook_type in ['postStart', 'preStop']:
            if hook_type in lifecycle:
                hook = lifecycle[hook_type]
                hook_id = self.generate_id("HOOK", 1)

                # Handler Type 결정
                handler_type = next(
                    (k for k in ['exec', 'httpGet', 'tcpSocket'] if k in hook),
                    None
                )
                if not handler_type:
                    continue

                handler_config = json.dumps(hook[handler_type])

                query = """
				INSERT INTO k8s_lifecycle_hooks (
					hook_id, container_id, hook_type,
					handler_type, handler_config
				) VALUES (%s, %s, %s, %s, %s)
				"""
                self.cursor.execute(query, (
                    hook_id,
                    container_id,
                    hook_type,
                    handler_type,
                    handler_config
                ))

    def insert_security_context(
            self,
            container_id: str,
            security_context: Dict[str, Any]
    ) -> None:
        """Security Context 저장"""
        context_id = self.generate_id("SEC", 1)
        query = """
		INSERT INTO k8s_security_contexts (
			context_id, container_id,
			capabilities_add, capabilities_drop,
			privileged, run_as_user, run_as_group,
			run_as_non_root, read_only_root_filesystem,
			allow_privilege_escalation
		) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
        self.cursor.execute(query, (
            context_id,
            container_id,
            json.dumps(security_context.get('capabilities', {}).get('add', [])),
            json.dumps(security_context.get('capabilities', {}).get('drop', [])),
            security_context.get('privileged', False),
            security_context.get('runAsUser'),
            security_context.get('runAsGroup'),
            security_context.get('runAsNonRoot', False),
            security_context.get('readOnlyRootFilesystem', False),
            security_context.get('allowPrivilegeEscalation', False)
        ))

    def insert_volumes(self, template_id: str, volumes: List[Dict[str, Any]]) -> None:
        """Volumes 저장"""
        for volume in volumes:
            volume_id = self.generate_id("VOL", 1)
            volume_type = next(iter(volume.keys() - {'name'}))
            volume_config = json.dumps(volume[volume_type])

            query = """
			INSERT INTO k8s_volumes (
				volume_id, template_id, volume_name,
				volume_type, volume_config
			) VALUES (%s, %s, %s, %s, %s)
			"""
            self.cursor.execute(query, (
                volume_id,
                template_id,
                volume['name'],
                volume_type,
                volume_config
            ))

    def insert_dns_config(self, template_id: str, dns_config: Dict[str, Any]) -> None:
        """DNS Config 저장"""
        config_id = self.generate_id("DNS", 1)
        query = """
        INSERT INTO k8s_dns_configs (
            config_id, template_id,  # deployment_id에서 template_id로 변경
            nameservers, searches, options
        ) VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(query, (
            config_id,
            template_id,  # 매개변수 그대로 사용
            json.dumps(dns_config.get('nameservers', [])),
            json.dumps(dns_config.get('searches', [])),
            json.dumps(dns_config.get('options', []))
        ))

    def insert_host_aliases(
            self,
            template_id: str,
            host_aliases: List[Dict[str, Any]]
    ) -> None:
        """Host Aliases 저장"""
        for alias in host_aliases:
            alias_id = self.generate_id("ALIAS", 1)
            query = """
            INSERT INTO k8s_host_aliases (
                alias_id, template_id, ip, hostnames  -- deployment_id에서 template_id로 변경
            ) VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (
                alias_id,
                template_id,  # 매개변수 그대로 사용
                alias['ip'],
                json.dumps(alias['hostnames'])
            ))

    def insert_topology_spread_constraints(
            self,
            template_id: str,
            constraints: List[Dict[str, Any]]
    ) -> None:
        """Topology Spread Constraints 저장"""
        for constraint in constraints:
            constraint_id = self.generate_id("TOP", 1)
            query = """
            INSERT INTO k8s_topology_spread_constraints (
                constraint_id, template_id,  -- deployment_id에서 template_id로 변경
                max_skew, topology_key,
                when_unsatisfiable, label_selector
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (
                constraint_id,
                template_id,  # 매개변수 그대로 사용
                constraint['maxSkew'],
                constraint['topologyKey'],
                constraint['whenUnsatisfiable'],
                json.dumps(constraint['labelSelector'])
            ))

    def close(self):
        """데이터베이스 연결 종료"""
        try:
            self.cursor.close()
            self.conn.close()
            logger.info("Database connection closed")
        except Error as e:
            logger.error(f"Error closing database connection: {e}")


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <input_file>")
        input_file = 'deployment_2.yaml'
    else:
        input_file = sys.argv[1]


    """메인 실행 함수"""
    # 데이터베이스 연결 정보
    db_config = {
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'kasugare',
        'password': 'uncsbjsa',
        'database': 'serving_test_2'
    }

    try:
        # YAML 파일 읽기
        with open(input_file, 'r') as f:
            deployment_data = yaml.safe_load(f)
        print(deployment_data)

        # DB 매니저 초기화
        manager = K8sDeploymentManager(**db_config)

        try:
            # Deployment 저장
            deployment_id = manager.insert_deployment(deployment_data)
            logger.info(f"Successfully inserted deployment: {deployment_id}")

        finally:
            manager.close()

    except Exception as e:
        logger.error(f"Error processing deployment: {e}")
        raise


if __name__ == "__main__":
    main()