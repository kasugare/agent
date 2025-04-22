import yaml
import mysql.connector
from mysql.connector import Error
import json
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class K8sDeploymentGenerator:
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
            logger.info(f"Database connection established")
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def get_deployment_yaml(self, deployment_name: str, namespace: str) -> Dict[str, Any]:
        """Deployment YAML 생성"""
        try:
            # 기본 구조 생성
            deployment_yaml = {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment'
            }

            # 1. Deployment 기본 정보 조회
            deployment = self.get_deployment_base(deployment_name, namespace)
            if not deployment:
                raise ValueError(f"Deployment {deployment_name} not found in namespace {namespace}")

            # 2. Metadata 설정
            deployment_yaml['metadata'] = self.get_metadata(deployment['deployment_id'])

            # 3. Spec 설정
            deployment_yaml['spec'] = self.get_deployment_spec(deployment)

            return deployment_yaml

        except Exception as e:
            logger.error(f"Error generating deployment YAML: {e}")
            raise

    def get_deployment_base(self, name: str, namespace: str) -> Optional[Dict[str, Any]]:
        """Deployment 기본 정보 조회"""
        query = """
		SELECT * FROM k8s_deployments 
		WHERE deployment_name = %s AND deployment_namespace = %s
		"""
        self.cursor.execute(query, (name, namespace))
        return self.cursor.fetchone()

    def get_metadata(self, deployment_id: str) -> Dict[str, Any]:
        """Metadata 정보 조회"""
        # 기본 정보 조회
        query = """
		SELECT deployment_name as name, deployment_namespace as namespace 
		FROM k8s_deployments WHERE deployment_id = %s
		"""
        self.cursor.execute(query, (deployment_id,))
        metadata = self.cursor.fetchone()

        # Labels 조회
        query = """
		SELECT label_key, label_value 
		FROM k8s_deployment_labels 
		WHERE deployment_id = %s
		"""
        self.cursor.execute(query, (deployment_id,))
        labels = {row['label_key']: row['label_value'] for row in self.cursor.fetchall()}
        if labels:
            metadata['labels'] = labels

        # Annotations 조회
        query = """
		SELECT annotation_key, annotation_value 
		FROM k8s_deployment_annotations 
		WHERE deployment_id = %s
		"""
        self.cursor.execute(query, (deployment_id,))
        annotations = {row['annotation_key']: row['annotation_value']
                       for row in self.cursor.fetchall()}
        if annotations:
            metadata['annotations'] = annotations

        return metadata

    def get_deployment_spec(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Deployment Spec 조회"""
        spec = {
            'replicas': deployment['replica_count'],
            'selector': self.get_deployment_selector(deployment['deployment_id']),
            'template': self.get_pod_template(deployment['deployment_id'])
        }

        # 추가 설정들
        if deployment['service_account_name']:
            spec['serviceAccountName'] = deployment['service_account_name']
        if deployment['automount_service_account_token'] is not None:
            spec['automountServiceAccountToken'] = deployment['automount_service_account_token']
        if deployment['host_network']:
            spec['hostNetwork'] = deployment['host_network']
        if deployment['dns_policy']:
            spec['dnsPolicy'] = deployment['dns_policy']
        if deployment['termination_grace_period_seconds']:
            spec['terminationGracePeriodSeconds'] = deployment['termination_grace_period_seconds']
        if deployment['restart_policy']:
            spec['restartPolicy'] = deployment['restart_policy']
        if deployment['priority_class_name']:
            spec['priorityClassName'] = deployment['priority_class_name']

        return spec

    def get_deployment_selector(self, deployment_id: str) -> Dict[str, Any]:
        """Deployment Selector 조회"""
        query = """
		SELECT label_key, label_value 
		FROM k8s_deployment_selectors 
		WHERE deployment_id = %s
		"""
        self.cursor.execute(query, (deployment_id,))
        selectors = self.cursor.fetchall()
        return {
            'matchLabels': {
                row['label_key']: row['label_value'] for row in selectors
            }
        }

    def get_pod_template(self, deployment_id: str) -> Dict[str, Any]:
        """Pod Template 조회"""
        # Template 기본 정보 조회
        query = """
		SELECT template_id 
		FROM k8s_pod_templates 
		WHERE deployment_id = %s
		"""
        self.cursor.execute(query, (deployment_id,))
        template = self.cursor.fetchone()
        if not template:
            return {}

        template_id = template['template_id']
        pod_template = {
            'metadata': self.get_pod_template_metadata(template_id),
            'spec': self.get_pod_template_spec(template_id)
        }

        return pod_template

    def get_pod_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """Pod Template Metadata 조회"""
        query = """
		SELECT label_key, label_value 
		FROM k8s_pod_template_labels 
		WHERE template_id = %s
		"""
        self.cursor.execute(query, (template_id,))
        labels = {row['label_key']: row['label_value']
                  for row in self.cursor.fetchall()}
        return {'labels': labels} if labels else {}

    def get_pod_template_spec(self, template_id: str) -> Dict[str, Any]:
        """Pod Template Spec 조회"""
        spec = {}

        # hostNetwork 조회
        query = """
        SELECT host_network FROM k8s_pod_templates WHERE template_id = %s
        """
        self.cursor.execute(query, (template_id,))
        template = self.cursor.fetchone()
        if template and template['host_network'] is not None:
            spec['hostNetwork'] = template['host_network']

        # nodeSelector 조회
        query = """
        SELECT label_key, label_value FROM k8s_node_selectors 
        WHERE template_id = %s
        """
        self.cursor.execute(query, (template_id,))
        selectors = self.cursor.fetchall()
        if selectors:
            spec['nodeSelector'] = {
                selector['label_key']: selector['label_value']
                for selector in selectors
            }

        # Affinity 조회
        affinity = self.get_affinity(template_id)
        if affinity:
            spec['affinity'] = affinity

        # Containers 조회
        containers = self.get_containers(template_id)
        if containers:
            spec['containers'] = containers

        # Volumes 조회
        volumes = self.get_volumes(template_id)
        if volumes:
            spec['volumes'] = volumes

        # DNS Config 조회
        dns_config = self.get_dns_config(template_id)
        if dns_config:
            spec['dnsConfig'] = dns_config

        # Host Aliases 조회
        host_aliases = self.get_host_aliases(template_id)
        if host_aliases:
            spec['hostAliases'] = host_aliases

        # Topology Spread Constraints 조회
        topology_constraints = self.get_topology_spread_constraints(template_id)
        if topology_constraints:
            spec['topologySpreadConstraints'] = topology_constraints

        return spec

    def get_affinity(self, template_id: str) -> Dict[str, Any]:
        """Affinity 설정 조회"""

        affinity = {}

        # Node Affinity 조회
        node_affinity = self.get_node_affinity(template_id)
        if node_affinity:
            affinity['nodeAffinity'] = node_affinity

        # Pod Affinity 조회
        pod_affinity = self.get_pod_affinity(template_id, 'podAffinity')
        if pod_affinity:
            affinity['podAffinity'] = pod_affinity

        # Pod Anti-Affinity 조회
        pod_anti_affinity = self.get_pod_affinity(template_id, 'podAntiAffinity')
        if pod_anti_affinity:
            affinity['podAntiAffinity'] = pod_anti_affinity

        return affinity if affinity else None


    def get_node_affinity(self, template_id: str) -> Dict[str, Any]:
        """Node Affinity 조회"""
        node_affinity = {}

        # Required Rules 조회
        query = """
            SELECT rule_id FROM k8s_node_affinity_rules 
            WHERE template_id = %s AND rule_type = 'required'
            """
        self.cursor.execute(query, (template_id,))
        required_rules = self.cursor.fetchall()

        if required_rules:
            node_terms = []
            for rule in required_rules:
                terms = self.get_node_selector_terms(rule['rule_id'])
                if terms:
                    node_terms.extend(terms)

            if node_terms:
                node_affinity['requiredDuringSchedulingIgnoredDuringExecution'] = {
                    'nodeSelectorTerms': node_terms
                }

        # Preferred Rules 조회
        query = """
            SELECT rule_id, weight FROM k8s_node_affinity_rules 
            WHERE template_id = %s AND rule_type = 'preferred'
            ORDER BY weight DESC
            """
        self.cursor.execute(query, (template_id,))
        preferred_rules = self.cursor.fetchall()

        if preferred_rules:
            preferred_terms = []
            for rule in preferred_rules:
                terms = self.get_node_selector_terms(rule['rule_id'])
                if terms:
                    for term in terms:
                        preferred_terms.append({
                            'weight': rule['weight'],
                            'preference': term
                        })

            if preferred_terms:
                node_affinity['preferredDuringSchedulingIgnoredDuringExecution'] = preferred_terms

        return node_affinity


    def get_node_selector_terms(self, rule_id: str) -> List[Dict[str, Any]]:
        """Node Selector Terms 조회"""
        query = """
            SELECT term_id FROM k8s_node_selector_terms 
            WHERE rule_id = %s ORDER BY term_order
            """
        self.cursor.execute(query, (rule_id,))
        terms = self.cursor.fetchall()

        selector_terms = []
        for term in terms:
            expressions = self.get_node_match_expressions(term['term_id'])
            if expressions:
                selector_terms.append({'matchExpressions': expressions})

        return selector_terms


    def get_node_match_expressions(self, term_id: str) -> List[Dict[str, Any]]:
        """Node Match Expressions 조회"""
        query = """
            SELECT expression_id, label_key, operator 
            FROM k8s_node_match_expressions 
            WHERE term_id = %s ORDER BY expression_order
            """
        self.cursor.execute(query, (term_id,))
        expressions = self.cursor.fetchall()

        match_expressions = []
        for expr in expressions:
            expression = {
                'key': expr['label_key'],
                'operator': expr['operator']
            }

            # Exists/DoesNotExist 연산자가 아닌 경우에만 values 조회
            if expr['operator'] not in ['Exists', 'DoesNotExist']:
                values = self.get_node_match_expression_values(expr['expression_id'])
                if values:
                    expression['values'] = values

            match_expressions.append(expression)

        return match_expressions


    def get_node_match_expression_values(self, expression_id: str) -> List[str]:
        """Node Match Expression Values 조회"""
        query = """
            SELECT label_value FROM k8s_node_match_expression_values 
            WHERE expression_id = %s ORDER BY value_order
            """
        self.cursor.execute(query, (expression_id,))
        values = self.cursor.fetchall()
        return [row['label_value'] for row in values]


    def get_pod_affinity(self, template_id: str, affinity_type: str) -> Dict[str, Any]:
        """Pod Affinity/Anti-Affinity 조회"""
        pod_affinity = {}

        # Required Rules 조회
        query = """
            SELECT rule_id, topology_key FROM k8s_pod_affinity_rules 
            WHERE template_id = %s AND affinity_type = %s AND rule_type = 'required'
            """
        self.cursor.execute(query, (template_id, affinity_type))
        required_rules = self.cursor.fetchall()

        if required_rules:
            required_terms = []
            for rule in required_rules:
                term = self.get_pod_affinity_term(rule['rule_id'], rule['topology_key'])
                if term:
                    required_terms.append(term)

            if required_terms:
                pod_affinity['requiredDuringSchedulingIgnoredDuringExecution'] = required_terms

        # Preferred Rules 조회
        query = """
            SELECT rule_id, weight, topology_key FROM k8s_pod_affinity_rules 
            WHERE template_id = %s AND affinity_type = %s AND rule_type = 'preferred'
            """
        self.cursor.execute(query, (template_id, affinity_type))
        preferred_rules = self.cursor.fetchall()

        if preferred_rules:
            preferred_terms = []
            for rule in preferred_rules:
                term = self.get_pod_affinity_term(rule['rule_id'], rule['topology_key'])
                if term:
                    preferred_terms.append({
                        'weight': rule['weight'],
                        'podAffinityTerm': term
                    })

            if preferred_terms:
                pod_affinity['preferredDuringSchedulingIgnoredDuringExecution'] = preferred_terms

        return pod_affinity


    def get_pod_affinity_term(self, rule_id: str, topology_key: str) -> Dict[str, Any]:
        """Pod Affinity Term 조회"""
        term = {'topologyKey': topology_key}

        # Label Selector 조회
        label_selector = self.get_pod_label_selector(rule_id)
        if label_selector:
            term['labelSelector'] = label_selector

        # Namespace Selector 조회
        namespace_selector = self.get_namespace_selector(rule_id)
        if namespace_selector:
            term['namespaceSelector'] = namespace_selector

        return term


    def get_pod_label_selector(self, rule_id: str) -> Dict[str, Any]:
        """Pod Label Selector 조회"""
        query = """
            SELECT selector_id FROM k8s_pod_label_selectors WHERE rule_id = %s
            """
        self.cursor.execute(query, (rule_id,))
        selector = self.cursor.fetchone()

        if selector:
            expressions = self.get_pod_match_expressions(selector['selector_id'])
            if expressions:
                return {'matchExpressions': expressions}

        return None


    def get_pod_match_expressions(self, selector_id: str) -> List[Dict[str, Any]]:
        """Pod Match Expressions 조회"""
        query = """
            SELECT expression_id, label_key, operator 
            FROM k8s_pod_match_expressions 
            WHERE selector_id = %s ORDER BY expression_order
            """
        self.cursor.execute(query, (selector_id,))
        expressions = self.cursor.fetchall()

        match_expressions = []
        for expr in expressions:
            expression = {
                'key': expr['label_key'],
                'operator': expr['operator']
            }

            if expr['operator'] not in ['Exists', 'DoesNotExist']:
                values = self.get_pod_match_expression_values(expr['expression_id'])
                if values:
                    expression['values'] = values

            match_expressions.append(expression)

        return match_expressions


    def get_pod_match_expression_values(self, expression_id: str) -> List[str]:
        """Pod Match Expression Values 조회"""
        query = """
            SELECT label_value FROM k8s_pod_match_expression_values 
            WHERE expression_id = %s ORDER BY value_order
            """
        self.cursor.execute(query, (expression_id,))
        values = self.cursor.fetchall()
        return [row['label_value'] for row in values]


    def get_namespace_selector(self, rule_id: str) -> Dict[str, Any]:
        """Namespace Selector 조회"""
        query = """
            SELECT selector_id FROM k8s_namespace_selectors WHERE rule_id = %s
            """
        self.cursor.execute(query, (rule_id,))
        selector = self.cursor.fetchone()

        if selector:
            query = """
                SELECT label_key, label_value 
                FROM k8s_namespace_match_labels 
                WHERE selector_id = %s
                """
            self.cursor.execute(query, (selector['selector_id'],))
            labels = self.cursor.fetchall()

            if labels:
                return {
                    'matchLabels': {
                        row['label_key']: row['label_value'] for row in labels
                    }
                }

        return None


    def get_containers(self, template_id: str) -> List[Dict[str, Any]]:


        """Containers 조회"""
        query = """
            SELECT * FROM k8s_containers WHERE template_id = %s
            """
        self.cursor.execute(query, (template_id,))
        containers = self.cursor.fetchall()

        container_list = []
        for container in containers:
            container_spec = {
                'name': container['container_name'],
                'image': f"{container['image_name']}:{container['image_tag']}"
            }

            if container['image_pull_policy']:
                container_spec['imagePullPolicy'] = container['image_pull_policy']

            if container['working_dir']:
                container_spec['workingDir'] = container['working_dir']

            if container['command']:
                print("- command", container.get('command'))
                container_spec['command'] = json.loads(container['command'])

            if container['args']:
                print("- args", container.get('args'))
                container_spec['args'] = json.loads(container['args'])

            # Resources 조회
            resources = self.get_container_resources(container['container_id'])
            if resources:
                container_spec['resources'] = resources

            # Ports 조회
            ports = self.get_container_ports(container['container_id'])
            if ports:
                container_spec['ports'] = ports

            # Env 조회
            env = self.get_container_env(container['container_id'])
            if env:
                container_spec['env'] = env

            # Volume Mounts 조회
            volume_mounts = self.get_volume_mounts(container['container_id'])
            if volume_mounts:
                container_spec['volumeMounts'] = volume_mounts

            # Probes 조회
            probes = self.get_container_probes(container['container_id'])
            container_spec.update(probes)

            # Lifecycle 조회
            lifecycle = self.get_container_lifecycle(container['container_id'])
            if lifecycle:
                container_spec['lifecycle'] = lifecycle

            # Security Context 조회
            security_context = self.get_container_security_context(container['container_id'])
            if security_context:
                container_spec['securityContext'] = security_context

            container_list.append(container_spec)

        return container_list


    def get_container_resources(self, container_id: str) -> Dict[str, Any]:
        """Container Resources 조회"""
        query = """
            SELECT resource_type, resource_name, request_amount, limit_amount 
            FROM k8s_container_resources 
            WHERE container_id = %s
            """
        self.cursor.execute(query, (container_id,))
        resources = self.cursor.fetchall()

        if not resources:
            return None

        resource_spec = {'requests': {}, 'limits': {}}
        for resource in resources:
            if resource['request_amount']:
                resource_spec['requests'][resource['resource_name']] = resource['request_amount']
            if resource['limit_amount']:
                resource_spec['limits'][resource['resource_name']] = resource['limit_amount']

        return resource_spec


    def get_container_ports(self, container_id: str) -> List[Dict[str, Any]]:
        """Container Ports 조회"""
        query = """
            SELECT port_name, container_port, protocol 
            FROM k8s_container_ports 
            WHERE container_id = %s
            """
        self.cursor.execute(query, (container_id,))
        ports = self.cursor.fetchall()

        if not ports:
            return None

        port_list = []
        for port in ports:
            port_spec = {'containerPort': port['container_port']}
            if port['port_name']:
                port_spec['name'] = port['port_name']
            port_spec['protocol'] = port['protocol']
            port_list.append(port_spec)

        return port_list


    def get_container_env(self, container_id: str) -> List[Dict[str, Any]]:
        """Container Environment Variables 조회"""
        query = """
            SELECT env_name, env_value_type, value_reference 
            FROM k8s_env_variables 
            WHERE container_id = %s
            """
        self.cursor.execute(query, (container_id,))
        env_vars = self.cursor.fetchall()

        if not env_vars:
            return None

        env_list = []
        for env in env_vars:
            env_spec = {'name': env['env_name']}

            if env['env_value_type'] == 'PLAIN':
                env_spec['value'] = json.loads(env['value_reference'])['value']
            else:
                value_from = {}
                ref_data = json.loads(env['value_reference'])

                if env['env_value_type'] == 'FIELD_REF':
                    value_from['fieldRef'] = {'fieldPath': ref_data['fieldPath']}
                elif env['env_value_type'] == 'SECRET':
                    value_from['secretKeyRef'] = ref_data
                elif env['env_value_type'] == 'CONFIG_MAP':
                    value_from['configMapKeyRef'] = ref_data

                env_spec['valueFrom'] = value_from

            env_list.append(env_spec)

        return env_list


    def get_volume_mounts(self, container_id: str) -> List[Dict[str, Any]]:
        """Volume Mounts 조회"""
        query = """
            SELECT volume_name, mount_path, sub_path, read_only 
            FROM k8s_volume_mounts 
            WHERE container_id = %s
            """
        self.cursor.execute(query, (container_id,))
        mounts = self.cursor.fetchall()

        if not mounts:
            return None

        mount_list = []
        for mount in mounts:
            mount_spec = {
                'name': mount['volume_name'],
                'mountPath': mount['mount_path']
            }
            if mount['sub_path']:
                mount_spec['subPath'] = mount['sub_path']
            if mount['read_only']:
                mount_spec['readOnly'] = mount['read_only']
            mount_list.append(mount_spec)

        return mount_list


    def get_container_probes(self, container_id: str) -> Dict[str, Any]:
        """Container Probes 조회"""
        query = """
            SELECT probe_type, handler_type, handler_config,
                   initial_delay_seconds, period_seconds,
                   timeout_seconds, success_threshold,
                   failure_threshold
            FROM k8s_probes 
            WHERE container_id = %s
            """
        self.cursor.execute(query, (container_id,))
        probes = self.cursor.fetchall()

        probe_specs = {}
        for probe in probes:
            probe_spec = {}

            # Handler 설정
            handler_config = json.loads(probe['handler_config'])
            probe_spec[probe['handler_type']] = handler_config

            # Timing 설정
            if probe['initial_delay_seconds']:
                probe_spec['initialDelaySeconds'] = probe['initial_delay_seconds']
            if probe['period_seconds']:
                probe_spec['periodSeconds'] = probe['period_seconds']
            if probe['timeout_seconds']:
                probe_spec['timeoutSeconds'] = probe['timeout_seconds']
            if probe['success_threshold']:
                probe_spec['successThreshold'] = probe['success_threshold']
            if probe['failure_threshold']:
                probe_spec['failureThreshold'] = probe['failure_threshold']

            probe_specs[f"{probe['probe_type']}Probe"] = probe_spec

        return probe_specs


    def get_container_lifecycle(self, container_id: str) -> Dict[str, Any]:
        """Container Lifecycle Hooks 조회"""
        query = """
            SELECT hook_type, handler_type, handler_config 
            FROM k8s_lifecycle_hooks 
            WHERE container_id = %s
            """
        self.cursor.execute(query, (container_id,))
        hooks = self.cursor.fetchall()

        if not hooks:
            return None

        lifecycle = {}
        for hook in hooks:
            print(hook)
            hook_spec = {
                hook['handler_type']: json.loads(hook['handler_config'])
            }
            print(hook_spec)
            lifecycle[hook['hook_type']] = hook_spec

        return lifecycle


    def get_container_security_context(self, container_id: str) -> Dict[str, Any]:
        """Container Security Context 조회"""
        query = """
            SELECT * FROM k8s_security_contexts 
            WHERE container_id = %s
            """
        self.cursor.execute(query, (container_id,))
        security = self.cursor.fetchone()

        if not security:
            return None

        security_context = {}

        if security['capabilities_add'] or security['capabilities_drop']:
            capabilities = {}
            if security['capabilities_add']:
                capabilities['add'] = json.loads(security['capabilities_add'])
            if security['capabilities_drop']:
                capabilities['drop'] = json.loads(security['capabilities_drop'])
            security_context['capabilities'] = capabilities

        if security['privileged'] is not None:
            security_context['privileged'] = security['privileged']
        if security['run_as_user'] is not None:
            security_context['runAsUser'] = security['run_as_user']
        if security['run_as_group'] is not None:
            security_context['runAsGroup'] = security['run_as_group']
        if security['run_as_non_root'] is not None:
            security_context['runAsNonRoot'] = security['run_as_non_root']
        if security['read_only_root_filesystem'] is not None:
            security_context['readOnlyRootFilesystem'] = security['read_only_root_filesystem']
        if security['allow_privilege_escalation'] is not None:
            security_context['allowPrivilegeEscalation'] = security['allow_privilege_escalation']

        return security_context


    def get_volumes(self, template_id: str) -> List[Dict[str, Any]]:
        """Volumes 조회"""
        query = """
            SELECT volume_name, volume_type, volume_config 
            FROM k8s_volumes 
            WHERE template_id = %s
            """
        self.cursor.execute(query, (template_id,))
        volumes = self.cursor.fetchall()

        if not volumes:
            return None

        volume_list = []
        for volume in volumes:
            volume_spec = {
                'name': volume['volume_name'],
                volume['volume_type']: json.loads(volume['volume_config'])
            }
            volume_list.append(volume_spec)

        return volume_list


    def get_dns_config(self, template_id: str) -> Dict[str, Any]:
        """DNS Config 조회"""
        query = """
            SELECT nameservers, searches, options 
            FROM k8s_dns_configs 
            WHERE template_id = %s
            """
        self.cursor.execute(query, (template_id,))
        dns = self.cursor.fetchone()

        if not dns:
            return None

        dns_config = {}
        if dns['nameservers']:
            dns_config['nameservers'] = json.loads(dns['nameservers'])
        if dns['searches']:
            dns_config['searches'] = json.loads(dns['searches'])
        if dns['options']:
            dns_config['options'] = json.loads(dns['options'])

        return dns_config


    def get_host_aliases(self, template_id: str) -> List[Dict[str, Any]]:
        """Host Aliases 조회"""
        query = """
            SELECT ip, hostnames 
            FROM k8s_host_aliases 
            WHERE template_id = %s
            """
        self.cursor.execute(query, (template_id,))
        aliases = self.cursor.fetchall()

        if not aliases:
            return None

        return [{
            'ip': alias['ip'],
            'hostnames': json.loads(alias['hostnames'])
        } for alias in aliases]


    def get_topology_spread_constraints(self, template_id: str) -> List[Dict[str, Any]]:
        """Topology Spread Constraints 조회"""
        query = """
            SELECT max_skew, topology_key, when_unsatisfiable, label_selector 
            FROM k8s_topology_spread_constraints 
            WHERE template_id = %s
            """
        self.cursor.execute(query, (template_id,))
        constraints = self.cursor.fetchall()

        if not constraints:
            return None

        return [{
            'maxSkew': constraint['max_skew'],
            'topologyKey': constraint['topology_key'],
            'whenUnsatisfiable': constraint['when_unsatisfiable'],
            'labelSelector': json.loads(constraint['label_selector'])
        } for constraint in constraints]


    def write_yaml_file(self, data: Dict[str, Any], file_path: str) -> None:
        """YAML 파일 작성"""
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


    def close(self):
        """데이터베이스 연결 종료"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("Database connection closed")
        except Error as e:
            logger.error(f"Error closing database connection: {e}")

    def to_k8s_bool(self, value: int) -> bool:
        """DB의 0/1값을 k8s용 boolean으로 변환"""
        return bool(value) if value is not None else None

    def get_deployment_spec(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Deployment Spec 조회"""
        spec = {
            'replicas': deployment['replica_count'],
            'selector': self.get_deployment_selector(deployment['deployment_id']),
            'template': self.get_pod_template(deployment['deployment_id'])
        }

        if deployment['service_account_name']:
            spec['serviceAccountName'] = deployment['service_account_name']

        if deployment['automount_service_account_token'] is not None:
            spec['automountServiceAccountToken'] = self.to_k8s_bool(
                deployment['automount_service_account_token']
            )

        if deployment['host_network'] is not None:
            spec['hostNetwork'] = self.to_k8s_bool(deployment['host_network'])

        if deployment['dns_policy']:
            spec['dnsPolicy'] = deployment['dns_policy']

        if deployment['termination_grace_period_seconds']:
            spec['terminationGracePeriodSeconds'] = deployment['termination_grace_period_seconds']

        if deployment['restart_policy']:
            spec['restartPolicy'] = deployment['restart_policy']

        if deployment['priority_class_name']:
            spec['priorityClassName'] = deployment['priority_class_name']

        return spec

    def get_pod_template_spec(self, template_id: str) -> Dict[str, Any]:
        """Pod Template Spec 조회"""
        spec = {}

        # hostNetwork 조회
        query = """
        SELECT host_network FROM k8s_pod_templates WHERE template_id = %s
        """
        self.cursor.execute(query, (template_id,))
        template = self.cursor.fetchone()
        if template and template['host_network'] is not None:
            spec['hostNetwork'] = self.to_k8s_bool(template['host_network'])

        # nodeSelector 조회
        query = """
        SELECT label_key, label_value FROM k8s_node_selectors 
        WHERE template_id = %s
        """
        self.cursor.execute(query, (template_id,))
        selectors = self.cursor.fetchall()
        if selectors:
            spec['nodeSelector'] = {
                selector['label_key']: selector['label_value']
                for selector in selectors
            }

        # Affinity 조회
        affinity = self.get_affinity(template_id)
        if affinity:
            spec['affinity'] = affinity

        # Containers 조회
        containers = self.get_containers(template_id)
        if containers:
            spec['containers'] = containers

        # Volumes 조회
        volumes = self.get_volumes(template_id)
        if volumes:
            spec['volumes'] = volumes

        return spec

    def get_volume_mounts(self, container_id: str) -> List[Dict[str, Any]]:
        """Volume Mounts 조회"""
        query = """
        SELECT volume_name, mount_path, sub_path, read_only 
        FROM k8s_volume_mounts 
        WHERE container_id = %s
        """
        self.cursor.execute(query, (container_id,))
        mounts = self.cursor.fetchall()

        if not mounts:
            return None

        mount_list = []
        for mount in mounts:
            mount_spec = {
                'name': mount['volume_name'],
                'mountPath': mount['mount_path']
            }
            if mount['sub_path']:
                mount_spec['subPath'] = mount['sub_path']
            if mount['read_only'] is not None:
                mount_spec['readOnly'] = self.to_k8s_bool(mount['read_only'])
            mount_list.append(mount_spec)

        return mount_list

    def get_container_security_context(self, container_id: str) -> Dict[str, Any]:
        """Container Security Context 조회"""
        query = """
        SELECT * FROM k8s_security_contexts 
        WHERE container_id = %s
        """
        self.cursor.execute(query, (container_id,))
        security = self.cursor.fetchone()

        if not security:
            return None

        security_context = {}

        if security['capabilities_add'] or security['capabilities_drop']:
            capabilities = {}
            if security['capabilities_add']:
                capabilities['add'] = json.loads(security['capabilities_add'])
            if security['capabilities_drop']:
                capabilities['drop'] = json.loads(security['capabilities_drop'])
            security_context['capabilities'] = capabilities

        if security['privileged'] is not None:
            security_context['privileged'] = self.to_k8s_bool(security['privileged'])
        if security['run_as_user'] is not None:
            security_context['runAsUser'] = security['run_as_user']
        if security['run_as_group'] is not None:
            security_context['runAsGroup'] = security['run_as_group']
        if security['run_as_non_root'] is not None:
            security_context['runAsNonRoot'] = self.to_k8s_bool(security['run_as_non_root'])
        if security['read_only_root_filesystem'] is not None:
            security_context['readOnlyRootFilesystem'] = self.to_k8s_bool(security['read_only_root_filesystem'])
        if security['allow_privilege_escalation'] is not None:
            security_context['allowPrivilegeEscalation'] = self.to_k8s_bool(security['allow_privilege_escalation'])

        return security_context

    def generate_deployment_yaml(self, deployment_name: str, namespace: str) -> Dict[str, Any]:
        """Deployment YAML 생성"""
        deployment_yaml = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment'
        }

        # 기본 정보 조회
        deployment = self.get_deployment_base(deployment_name, namespace)
        if not deployment:
            raise ValueError(f"Deployment {deployment_name} not found in namespace {namespace}")

        # Metadata 설정
        deployment_yaml['metadata'] = self.get_metadata(deployment['deployment_id'])

        # Spec 설정
        deployment_yaml['spec'] = self.get_deployment_spec(deployment)

        return deployment_yaml

    def write_deployment_yaml(self, deployment_name: str, namespace: str, output_file: str):
        """Deployment YAML 파일 생성"""
        deployment_yaml = self.generate_deployment_yaml(deployment_name, namespace)

        # YAML 파일 작성
        with open(output_file, 'w') as f:
            yaml.dump(deployment_yaml, f, default_flow_style=False, sort_keys=False)


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <input_file>")
        return

    input_file = sys.argv[1]

    """메인 실행 함수"""
    db_config = {
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'kasugare',
        'password': 'uncsbjsa',
        'database': 'serving_test_2'
    }

    try:
        generator = K8sDeploymentGenerator(**db_config)
        deployment_yaml = generator.get_deployment_yaml(
            deployment_name='complete-deploy-demo-5',
            namespace='deploy-demo-5'
        )

        # YAML 파일 생성
        generator.write_yaml_file(deployment_yaml, 'generated_deployment.yaml')
        logger.info("Successfully generated deployment YAML")

    except Exception as e:
        logger.error(f"Error generating deployment YAML: {e}")
        raise
    finally:
        if 'generator' in locals():
            generator.close()


if __name__ == "__main__":
    main()
