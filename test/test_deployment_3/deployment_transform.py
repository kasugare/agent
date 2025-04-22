
import time
import json
# import uuid
from typing import Dict, Any

# deployment_transformer.py
class DeploymentTransformer:
    def __init__(self, logger):
        self._logger = logger

    def generate_id(self, prefix: str, sequence:str = None) -> str:
        """고유 ID 생성"""
        timestamp = int(time.time() * 100000)
        if sequence:
            id = f"{prefix}_{timestamp}_{sequence:04d}"
        else:
            id = f"{prefix}_{timestamp}"
        return id

    def transform_deployment(self, deployment_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deployment 데이터를 DB 구조에 맞게 변환
        """
        app_id = self.generate_id("APP")
        deployment_id = self.generate_id("DEP")
        template_id = self.generate_id("TPL")

        spec = deployment_dict['spec']
        template_spec = spec['template']['spec']

        transformed = {
            'application': {
                'app_id': app_id,
                'app_name': deployment_dict['metadata']['name'],
                'app_namespace': deployment_dict['metadata']['namespace'],
                'app_status': 'ACTIVE'
            },
            'deployment': {
                'deployment_id': deployment_id,
                'app_id': app_id,
                'deployment_name': deployment_dict['metadata']['name'],
                'deployment_namespace': deployment_dict['metadata']['namespace'],
                'replica_count': spec['replicas'],
                'strategy_type': spec.get('strategy', {}).get('type', 'RollingUpdate'),
                'service_account_name': template_spec.get('serviceAccountName'),
                'automount_service_account_token': template_spec.get('automountServiceAccountToken', True),
                'host_network': template_spec.get('hostNetwork', False),
                'dns_policy': template_spec.get('dnsPolicy', 'ClusterFirst'),
                'priority_class_name': template_spec.get('priorityClassName'),
                'restart_policy': template_spec.get('restartPolicy', 'Always'),
                'termination_grace_period_seconds': template_spec.get('terminationGracePeriodSeconds', 30)
            }
        }

        # Labels, Annotations, Selectors 변환
        transformed['deployment_labels'] = [
            {
                'label_id': self.generate_id("TLBL", 1),
                'deployment_id': deployment_id,
                'label_key': key,
                'label_value': str(value)  # 값을 문자열로 변환
            }
            for key, value in deployment_dict['metadata'].get('labels', {}).items()
        ]

        transformed['deployment_annotations'] = [
            {
                'annotation_id': self.generate_id("ANN", 1),
                'deployment_id': deployment_id,
                'annotation_key': key,
                'annotation_value': str(value)  # 값을 문자열로 변환
            }
            for key, value in deployment_dict['metadata'].get('annotations', {}).items()
        ]

        transformed['deployment_selectors'] = [
            {
                'selector_id': self.generate_id("SEL", 1),
                'deployment_id': deployment_id,
                'label_key': key,
                'label_value': str(value)  # 값을 문자열로 변환
            }
            for key, value in spec.get('selector', {}).get('matchLabels', {}).items()
        ]

        # Pod Template 변환
        transformed['pod_template'] = self._transform_pod_template(template_spec, template_id, deployment_id)

        # Node Affinity 및 Pod Affinity 변환
        if 'affinity' in template_spec:
            affinity = template_spec['affinity']
            if 'nodeAffinity' in affinity:
                transformed['node_affinity'] = self._transform_node_affinity(
                    affinity['nodeAffinity'],
                    template_id
                )
            if 'podAffinity' in affinity:
                transformed['pod_affinity'] = self._transform_pod_affinity(
                    affinity['podAffinity'],
                    template_id,
                    'podAffinity'
                )
            if 'podAntiAffinity' in affinity:
                transformed['pod_anti_affinity'] = self._transform_pod_affinity(
                    affinity['podAntiAffinity'],
                    template_id,
                    'podAntiAffinity'
                )

        # Container 및 Volume 변환
        transformed['containers'] = self._transform_containers(template_spec.get('containers', []), template_id)
        if 'volumes' in template_spec:
            transformed['volumes'] = self._transform_volumes(template_spec['volumes'], template_id)

        return transformed

    def _transform_pod_template(self, template_spec: Dict[str, Any], template_id: str, deployment_id: str) -> Dict[str, Any]:
        """Pod Template 데이터 변환"""
        template = {
            'template_id': template_id,
            'deployment_id': deployment_id,
            'host_network': template_spec.get('hostNetwork', False)
        }

        # Node Selector 변환
        if 'nodeSelector' in template_spec:
            template['node_selectors'] = [
                {
                    'selector_id': self.generate_id("NS"),
                    'template_id': template_id,
                    'label_key': key,
                    'label_value': value
                }
                for key, value in template_spec['nodeSelector'].items()
            ]

        # DNS Config 변환
        if 'dnsConfig' in template_spec:
            dns_config = template_spec['dnsConfig']
            template['dns_config'] = {
                'config_id': self.generate_id("DNS"),
                'template_id': template_id,
                'nameservers': json.dumps(dns_config.get('nameservers', [])),
                'searches': json.dumps(dns_config.get('searches', [])),
                'options': json.dumps(dns_config.get('options', []))
            }

        # Host Aliases 변환
        if 'hostAliases' in template_spec:
            template['host_aliases'] = [
                {
                    'alias_id': self.generate_id("ALIAS"),
                    'template_id': template_id,
                    'ip': alias['ip'],
                    'hostnames': json.dumps(alias['hostnames'])
                }
                for alias in template_spec['hostAliases']
            ]

        # Topology Spread Constraints 변환
        if 'topologySpreadConstraints' in template_spec:
            template['topology_spread_constraints'] = [
                {
                    'constraint_id': self.generate_id("TOP"),
                    'template_id': template_id,
                    'max_skew': constraint['maxSkew'],
                    'topology_key': constraint['topologyKey'],
                    'when_unsatisfiable': constraint['whenUnsatisfiable'],
                    'label_selector': json.dumps(constraint['labelSelector'])
                }
                for constraint in template_spec['topologySpreadConstraints']
            ]

        return template

    def _transform_containers(self, containers: list, template_id: str) -> list:
        """Container 데이터 상세 변환"""
        result = []
        container_base_id = self.generate_id("CONT")
        for index, container in enumerate(containers, 1):
            container_id = f"{container_base_id}_{index}"
            container_data = {
                'container_id': container_id,
                'template_id': template_id,
                'container_name': container['name'],
                'image_name': container['image'].split(':')[0],
                'image_tag': container['image'].split(':')[1] if ':' in container['image'] else 'latest',
                'image_pull_policy': container.get('imagePullPolicy', 'IfNotPresent'),
                'working_dir': container.get('workingDir'),
                'command': json.dumps(container.get('command', [])),
                'args': json.dumps(container.get('args', [])),
            }

            # Resources
            if 'resources' in container:
                container_data['resources'] = self._transform_resources(container['resources'], container_id)

            # Ports
            if 'ports' in container:
                container_data['ports'] = [
                    {
                        'port_id': self.generate_id("PORT"),
                        'container_id': container_id,
                        'port_name': port.get('name'),
                        'container_port': port['containerPort'],
                        'protocol': port.get('protocol', 'TCP')
                    }
                    for port in container['ports']
                ]

            # Environment Variables
            if 'env' in container:
                container_data['env_variables'] = self._transform_env_variables(container['env'], container_id)

            # Volume Mounts
            if 'volumeMounts' in container:
                container_data['volume_mounts'] = [
                    {
                        'mount_id': self.generate_id("MOUNT"),
                        'container_id': container_id,
                        'volume_name': mount['name'],
                        'mount_path': mount['mountPath'],
                        'sub_path': mount.get('subPath'),
                        'read_only': mount.get('readOnly', False)
                    }
                    for mount in container['volumeMounts']
                ]

            # Probes
            container_data['probes'] = self._transform_probes(container, container_id)

            # Security Context
            if 'securityContext' in container:
                container_data['security_context'] = {
                    'context_id': self.generate_id("SEC"),
                    'container_id': container_id,
                    'capabilities_add': json.dumps(container['securityContext'].get('capabilities', {}).get('add', [])),
                    'capabilities_drop': json.dumps(container['securityContext'].get('capabilities', {}).get('drop', [])),
                    'privileged': container['securityContext'].get('privileged', False),
                    'run_as_user': container['securityContext'].get('runAsUser'),
                    'run_as_group': container['securityContext'].get('runAsGroup'),
                    'run_as_non_root': container['securityContext'].get('runAsNonRoot', False),
                    'read_only_root_filesystem': container['securityContext'].get('readOnlyRootFilesystem', False),
                    'allow_privilege_escalation': container['securityContext'].get('allowPrivilegeEscalation', False)
                }

            # Lifecycle
            if 'lifecycle' in container:
                container_data['lifecycle_hooks'] = self._transform_lifecycle_hooks(container['lifecycle'], container_id)

            result.append(container_data)
        return result

    def _transform_env_variables(self, env_vars: list, container_id: str) -> list:
        """Environment Variables 변환"""
        result = []
        env_base_id = self.generate_id("ENV")
        for index, env in enumerate(env_vars, 1):
            env_data = {
                'env_id': f"{env_base_id}_{index}",
                'container_id': container_id,
                'env_name': env['name']
            }

            if 'value' in env:
                env_data['env_value_type'] = 'PLAIN'
                env_data['value_reference'] = json.dumps({'value': env['value']})
            elif 'valueFrom' in env:
                value_from = env['valueFrom']
                if 'fieldRef' in value_from:
                    env_data['env_value_type'] = 'FIELD_REF'
                    env_data['value_reference'] = json.dumps(value_from['fieldRef'])
                elif 'configMapKeyRef' in value_from:
                    env_data['env_value_type'] = 'CONFIG_MAP'
                    env_data['value_reference'] = json.dumps(value_from['configMapKeyRef'])
                elif 'secretKeyRef' in value_from:
                    env_data['env_value_type'] = 'SECRET'
                    env_data['value_reference'] = json.dumps(value_from['secretKeyRef'])

            result.append(env_data)
        return result

    def _transform_probes(self, container: Dict[str, Any], container_id: str) -> list:
        """Container Probes 변환"""
        result = []
        probe_types = ['livenessProbe', 'readinessProbe', 'startupProbe']

        probe_base_id = self.generate_id("PROBE"),
        for index, probe_type in enumerate(probe_types, 1):
            if probe_type in container:
                probe = container[probe_type]
                probe_data = {
                    'probe_id': f"{probe_base_id}_{index}",
                    'container_id': container_id,
                    'probe_type': probe_type.replace('Probe', ''),
                    'initial_delay_seconds': probe.get('initialDelaySeconds'),
                    'period_seconds': probe.get('periodSeconds'),
                    'timeout_seconds': probe.get('timeoutSeconds'),
                    'success_threshold': probe.get('successThreshold'),
                    'failure_threshold': probe.get('failureThreshold')
                }

                # Handler 타입 및 설정 결정
                if 'exec' in probe:
                    probe_data['handler_type'] = 'exec'
                    probe_data['handler_config'] = json.dumps(probe['exec'])
                elif 'httpGet' in probe:
                    probe_data['handler_type'] = 'httpGet'
                    probe_data['handler_config'] = json.dumps(probe['httpGet'])
                elif 'tcpSocket' in probe:
                    probe_data['handler_type'] = 'tcpSocket'
                    probe_data['handler_config'] = json.dumps(probe['tcpSocket'])

                result.append(probe_data)

        return result

    def _transform_security_context(self, security_context: Dict[str, Any], container_id: str) -> Dict[str, Any]:
        """Security Context 변환"""
        if not security_context:
            return None

        return {
            'context_id': self.generate_id("SEC", 1),
            'container_id': container_id,
            'capabilities_add': json.dumps(security_context.get('capabilities', {}).get('add', [])),
            'capabilities_drop': json.dumps(security_context.get('capabilities', {}).get('drop', [])),
            'privileged': security_context.get('privileged', False),
            'run_as_user': security_context.get('runAsUser'),
            'run_as_group': security_context.get('runAsGroup'),
            'run_as_non_root': security_context.get('runAsNonRoot', False),
            'read_only_root_filesystem': security_context.get('readOnlyRootFilesystem', False),
            'allow_privilege_escalation': security_context.get('allowPrivilegeEscalation', False)
        }

    def _transform_lifecycle_hooks(self, lifecycle: Dict[str, Any], container_id: str) -> list:
        """Lifecycle Hooks 변환"""
        result = []

        if not lifecycle:
            return result

        for hook_type in ['postStart', 'preStop']:
            if hook_type in lifecycle:
                hook = lifecycle[hook_type]
                hook_data = {
                    'hook_id': self.generate_id("HOOK", 1),
                    'container_id': container_id,
                    'hook_type': hook_type
                }

                if 'exec' in hook:
                    hook_data['handler_type'] = 'exec'
                    hook_data['handler_config'] = json.dumps(hook['exec'])
                elif 'httpGet' in hook:
                    hook_data['handler_type'] = 'httpGet'
                    hook_data['handler_config'] = json.dumps(hook['httpGet'])
                elif 'tcpSocket' in hook:
                    hook_data['handler_type'] = 'tcpSocket'
                    hook_data['handler_config'] = json.dumps(hook['tcpSocket'])

                result.append(hook_data)

        return result

    def _transform_node_affinity(self, node_affinity: Dict[str, Any], template_id: str) -> Dict[str, Any]:
        """Node Affinity 데이터 변환"""
        result = {'rules': []}

        # Required Node Affinity
        required = node_affinity.get('requiredDuringSchedulingIgnoredDuringExecution', {})
        if required:
            rule_id = self.generate_id("NAR")
            result['rules'].append({
                'rule_id': rule_id,
                'template_id': template_id,
                'rule_type': 'required',
                'weight': None,
                'terms': self._transform_match_expressions_terms(
                    required.get('nodeSelectorTerms', []),
                    rule_id
                )
            })

        # Preferred Node Affinity
        preferred = node_affinity.get('preferredDuringSchedulingIgnoredDuringExecution', [])
        for idx, pref in enumerate(preferred, 1):
            rule_id = self.generate_id("PAR", idx + 100)
            result['rules'].append({
                'rule_id': rule_id,
                'template_id': template_id,
                'rule_type': 'preferred',
                'weight': pref.get('weight', 1),
                'terms': self._transform_match_expressions_terms(
                    [pref['preference']],
                    rule_id
                )
            })

        return result

    def _transform_match_expressions_terms(self, terms: list, rule_id: str) -> list:
        """Match Expression Terms 변환"""
        result = []
        for term_idx, term in enumerate(terms):
            term_id = self.generate_id("MET", term_idx)
            term_data = {
                'term_id': term_id,
                'rule_id': rule_id,
                'term_order': term_idx,
                'expressions': []
            }

            for expr_idx, expr in enumerate(term.get('matchExpressions', [])):
                expression_id = self.generate_id("MEE", expr_idx)
                expression = {
                    'expression_id': expression_id,
                    'term_id': term_id,
                    'label_key': expr['key'],
                    'operator': expr['operator'],
                    'expression_order': expr_idx,
                    'values': []
                }

                if 'values' in expr:
                    expression['values'] = [
                        {
                            'value_id': self.generate_id("MEV", expr_idx),
                            'expression_id': expression_id,
                            'label_value': value,
                            'value_order': val_idx
                        }
                        for val_idx, value in enumerate(expr['values'])
                    ]

                term_data['expressions'].append(expression)

            result.append(term_data)
        return result

    def _transform_pod_affinity(self, affinity_data: Dict[str, Any], template_id: str, affinity_type: str) -> Dict[str, Any]:
        """Pod Affinity/AntiAffinity 데이터 변환"""
        result = {'rules': []}

        # Required Affinity
        required = affinity_data.get('requiredDuringSchedulingIgnoredDuringExecution', [])
        for req in required:
            rule_id = self.generate_id("NAR", 1)
            rule = {
                'rule_id': rule_id,
                'template_id': template_id,
                'affinity_type': affinity_type,
                'rule_type': 'required',
                'weight': None,
                'topology_key': req['topologyKey']
            }

            # Label Selector 처리
            if 'labelSelector' in req:
                selector_id = self.generate_id("PALS", 1)
                rule['label_selector'] = {
                    'selector_id': selector_id,
                    'rule_id': rule_id,
                    'expressions': self._transform_pod_match_expressions(
                        req['labelSelector'].get('matchExpressions', []),
                        selector_id
                    )
                }

            # Namespace Selector 처리
            if 'namespaceSelector' in req:
                selector_id = self.generate_id("PANS", 1)
                rule['namespace_selector'] = {
                    'selector_id': selector_id,
                    'rule_id': rule_id,
                    'labels': [
                        {
                            'label_id': self.generate_id("PANSL", 1),
                            'selector_id': selector_id,
                            'label_key': key,
                            'label_value': value
                        }
                        for key, value in req['namespaceSelector'].get('matchLabels', {}).items()
                    ]
                }

            result['rules'].append(rule)

        # Preferred Affinity
        preferred = affinity_data.get('preferredDuringSchedulingIgnoredDuringExecution', [])
        for idx, pref in enumerate(preferred, 1):
            rule_id = self.generate_id("PAR", idx + 100)
            rule = {
                'rule_id': rule_id,
                'template_id': template_id,
                'affinity_type': affinity_type,
                'rule_type': 'preferred',
                'weight': pref.get('weight', 1),
                'topology_key': pref['podAffinityTerm']['topologyKey']
            }

            # Label Selector 처리
            if 'labelSelector' in pref['podAffinityTerm']:
                selector_id = self.generate_id("PAT", 1)
                rule['label_selector'] = {
                    'selector_id': selector_id,
                    'rule_id': rule_id,
                    'expressions': self._transform_pod_match_expressions(
                        pref['podAffinityTerm']['labelSelector'].get('matchExpressions', []),
                        selector_id
                    )
                }

            result['rules'].append(rule)

        return result

    def _transform_pod_match_expressions(self, expressions: list, selector_id: str) -> list:
        """Pod Match Expressions 변환"""
        result = []
        for expr_idx, expr in enumerate(expressions):
            print(selector_id, expr_idx, expr)
            expression_id = self.generate_id("PME", expr_idx)
            expression = {
                'expression_id': expression_id,
                'selector_id': selector_id,
                'label_key': expr['key'],
                'operator': expr['operator'],
                'expression_order': expr_idx,
                'values': []
            }

            if 'values' in expr:
                expression['values'] = [
                    {
                        'value_id': self.generate_id("PMEV", expr_idx),
                        'expression_id': expression_id,
                        'label_value': value,
                        'value_order': val_idx
                    }
                    for val_idx, value in enumerate(expr['values'])
                ]

            result.append(expression)
        return result


    def _transform_resources(self, resources: Dict[str, Any], container_id: str) -> list:
        """Container Resources 데이터 변환"""
        result = []
        resource_type_mapping = {
            'cpu': 'CPU',
            'memory': 'MEMORY',
            'nvidia.com/gpu': 'GPU'
        }

        requests = resources.get('requests', {})
        limits = resources.get('limits', {})

        # 모든 리소스 키를 수집
        all_resources = set(list(requests.keys()) + list(limits.keys()))

        for resource_name in all_resources:
            resource_data = {
                'resource_id': self.generate_id("RES", 1),
                'container_id': container_id,
                'resource_type': resource_type_mapping.get(resource_name.lower(), 'CUSTOM'),
                'resource_name': resource_name,
                'request_amount': str(requests.get(resource_name)) if resource_name in requests else None,
                'limit_amount': str(limits.get(resource_name)) if resource_name in limits else None
            }
            result.append(resource_data)

        return result

    def _transform_volumes(self, volumes: list, template_id: str) -> list:
        """Volume 데이터 변환"""
        return [
            {
                'volume_id': self.generate_id("VOL", 1),
                'template_id': template_id,
                'volume_name': volume['name'],
                'volume_type': next((k for k in volume.keys() if k != 'name'), None),
                'volume_config': json.dumps(volume)
            }
            for volume in volumes
        ]
