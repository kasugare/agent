import mysql.connector
from typing import Dict, Any


class DeploymentAccess:
    def __init__(self, logger, db_config):
        self._logger = logger
        self.db_config = db_config

    def _convert_bool_to_int(self, value: bool) -> int:
        """Boolean 값을 MySQL TINYINT(1)로 변환"""
        return 1 if value else 0

    def insert_deployment(self, data: Dict[str, Any]) -> str:
        """
        Deployment 데이터를 DB에 저장
        """
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)

            self._logger.info("# Step 01: Application 저장")
            self._insert_application(cursor, data['application'])

            self._logger.info("# Step 02: Deployment 저장")
            self._insert_deployment_main(cursor, data['deployment'])

            self._logger.info("# Step 03: Labels 저장")
            if 'deployment_labels' in data:
                for label in data['deployment_labels']:
                    self._insert_deployment_label(cursor, label)

            self._logger.info("# Step 04: Annotations 저장")
            if 'deployment_annotations' in data:
                for annotation in data['deployment_annotations']:
                    self._insert_deployment_annotation(cursor, annotation)

            self._logger.info("# Step 05: Pod Template 저장")
            if 'pod_template' in data:
                self._insert_pod_template(cursor, data['pod_template'])

            self._logger.info("# Step 06: Node Affinity 저장")
            if 'node_affinity' in data:
                self._insert_node_affinity(cursor, data['node_affinity'])

            self._logger.info("# Step 07: Pod Affinity 저장")
            if 'pod_affinity' in data:
                self._insert_pod_affinity(cursor, data['pod_affinity'])

            self._logger.info("# Step 08: Containers 저장")
            if 'containers' in data:
                for container in data['containers']:
                    self._insert_container(cursor, container)

            self._logger.info("# Step 09: Volumes 저장")
            if 'volumes' in data:
                for volume in data['volumes']:
                    self._insert_volume(cursor, volume)

            conn.commit()
            return data['deployment']['deployment_id']

        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Failed to create deployment: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _insert_application(self, cursor, app_data):
        sql = """
        INSERT INTO k8s_applications (
            app_id, app_name, app_namespace, app_status
        ) VALUES (
            %(app_id)s, %(app_name)s, %(app_namespace)s, %(app_status)s
        )
        """
        cursor.execute(sql, app_data)

    def _insert_deployment_main(self, cursor, deployment_data):
        """Deployment 메인 데이터 저장"""
        deployment_insert_data = {
            'deployment_id': deployment_data['deployment_id'],
            'app_id': deployment_data['app_id'],
            'deployment_name': deployment_data['deployment_name'],
            'deployment_namespace': deployment_data['deployment_namespace'],
            'replica_count': deployment_data['replica_count'],
            'strategy_type': deployment_data.get('strategy_type', 'RollingUpdate'),
            'service_account_name': deployment_data.get('service_account_name'),
            'automount_service_account_token': self._convert_bool_to_int(deployment_data.get('automount_service_account_token', True)),
            'host_network': self._convert_bool_to_int(deployment_data.get('host_network', False)),
            'dns_policy': deployment_data.get('dns_policy', 'ClusterFirst'),
            'priority_class_name': deployment_data.get('priority_class_name'),
            'restart_policy': deployment_data.get('restart_policy', 'Always'),
            'termination_grace_period_seconds': deployment_data.get('termination_grace_period_seconds', 30)
        }

        sql = """
        INSERT INTO k8s_deployments (
            deployment_id, app_id, deployment_name, deployment_namespace,
            replica_count, strategy_type, service_account_name,
            automount_service_account_token, host_network, dns_policy,
            priority_class_name, restart_policy, termination_grace_period_seconds
        ) VALUES (
            %(deployment_id)s, %(app_id)s, %(deployment_name)s,
            %(deployment_namespace)s, %(replica_count)s, %(strategy_type)s,
            %(service_account_name)s, %(automount_service_account_token)s,
            %(host_network)s, %(dns_policy)s, %(priority_class_name)s,
            %(restart_policy)s, %(termination_grace_period_seconds)s
        )
        """
        cursor.execute(sql, deployment_insert_data)

    def _insert_deployment_label(self, cursor, label_data):
        sql = """
        INSERT INTO k8s_deployment_labels (
            label_id, deployment_id, label_key, label_value
        ) VALUES (
            %(label_id)s, %(deployment_id)s, %(label_key)s, %(label_value)s
        )
        """
        cursor.execute(sql, label_data)

    def _insert_deployment_annotation(self, cursor, annotation_data):
        sql = """
        INSERT INTO k8s_deployment_annotations (
            annotation_id, deployment_id, annotation_key, annotation_value
        ) VALUES (
            %(annotation_id)s, %(deployment_id)s, %(annotation_key)s, %(annotation_value)s
        )
        """
        cursor.execute(sql, annotation_data)

    def _insert_container(self, cursor, container_data):
        # 기본 Container 정보 저장
        sql = """
        INSERT INTO k8s_containers (
            container_id, template_id, container_name, image_name,
            image_tag, image_pull_policy, working_dir, command, args
        ) VALUES (
            %(container_id)s, %(template_id)s, %(container_name)s,
            %(image_name)s, %(image_tag)s, %(image_pull_policy)s,
            %(working_dir)s, %(command)s, %(args)s
        )
        """
        container_param = {
            'container_id': container_data['container_id'],
            'template_id': container_data['template_id'],
            'container_name': container_data['container_name'],
            'image_name': container_data['image_name'],
            'image_tag': container_data['image_tag'],
            'image_pull_policy': container_data['image_pull_policy'],
            'working_dir': container_data['working_dir'],
            'command': container_data['command'],
            'args': container_data['args']
        }
        cursor.execute(sql, container_param)

        self._logger.info(" -- Ports 저장")
        if 'ports' in container_data:
            for port in container_data['ports']:
                self._insert_container_port(cursor, port)

        self._logger.info(" -- Environment Variables 저장")
        if 'env_variables' in container_data:
            for env_var in container_data['env_variables']:
                self._insert_env_variable(cursor, env_var)

        self._logger.info(" -- Volume Mounts 저장")
        if 'volume_mounts' in container_data:
            for mount in container_data['volume_mounts']:
                self._insert_volume_mount(cursor, mount)

        self._logger.info(" -- Resources 저장")
        if 'resources' in container_data:
            for resource in container_data['resources']:
                self._insert_container_resource(cursor, resource)

        self._logger.info(" -- Security Context 저장")
        if 'security_context' in container_data:
            self._insert_security_context(cursor, container_data['security_context'])

    def _insert_container_port(self, cursor, port_data):
        sql = """
        INSERT INTO k8s_container_ports (
            port_id, container_id, port_name, container_port, protocol
        ) VALUES (
            %(port_id)s, %(container_id)s, %(port_name)s,
            %(container_port)s, %(protocol)s
        )
        """
        cursor.execute(sql, port_data)

    def _insert_env_variable(self, cursor, env_data):
        sql = """
        INSERT INTO k8s_env_variables (
            env_id, container_id, env_name, env_value_type, value_reference
        ) VALUES (
            %(env_id)s, %(container_id)s, %(env_name)s,
            %(env_value_type)s, %(value_reference)s
        )
        """
        cursor.execute(sql, env_data)

    def _insert_volume_mount(self, cursor, mount_data):
        """Volume Mount 데이터 저장"""
        mount_insert_data = {
            'mount_id': mount_data['mount_id'],
            'container_id': mount_data['container_id'],
            'volume_name': mount_data['volume_name'],
            'mount_path': mount_data['mount_path'],
            'sub_path': mount_data.get('sub_path'),
            'read_only': self._convert_bool_to_int(mount_data.get('read_only', False))
        }

        sql = """
        INSERT INTO k8s_volume_mounts (
            mount_id, container_id, volume_name, mount_path,
            sub_path, read_only
        ) VALUES (
            %(mount_id)s, %(container_id)s, %(volume_name)s,
            %(mount_path)s, %(sub_path)s, %(read_only)s
        )
        """
        cursor.execute(sql, mount_insert_data)

    def _insert_container_resource(self, cursor, resource_data):
        sql = """
        INSERT INTO k8s_container_resources (
            resource_id, container_id, resource_type,
            resource_name, request_amount, limit_amount
        ) VALUES (
            %(resource_id)s, %(container_id)s, %(resource_type)s,
            %(resource_name)s, %(request_amount)s, %(limit_amount)s
        )
        """
        cursor.execute(sql, resource_data)

    def _insert_volume(self, cursor, volume_data):
        sql = """
        INSERT INTO k8s_volumes (
            volume_id, template_id, volume_name, volume_type, volume_config
        ) VALUES (
            %(volume_id)s, %(template_id)s, %(volume_name)s,
            %(volume_type)s, %(volume_config)s
        )
        """
        cursor.execute(sql, volume_data)

    def _insert_pod_template(self, cursor, template_data):
        """Pod Template 데이터 저장"""
        self._logger.info(" -- 기본 template 정보 저장")
        template_insert_data = {
            'template_id': template_data['template_id'],
            'deployment_id': template_data['deployment_id'],
            'host_network': self._convert_bool_to_int(template_data.get('host_network', False))
        }
        sql = """
        INSERT INTO k8s_pod_templates (
            template_id, deployment_id, host_network
        ) VALUES (
            %(template_id)s, %(deployment_id)s, %(host_network)s
        )
        """
        cursor.execute(sql, template_insert_data)

        self._logger.info(" -- Node Selector 저장")
        if 'node_selectors' in template_data:
            for selector in template_data['node_selectors']:
                sql = """
                INSERT INTO k8s_node_selectors (
                    selector_id, template_id, label_key, label_value
                ) VALUES (
                    %(selector_id)s, %(template_id)s, %(label_key)s, %(label_value)s
                )
                """
                cursor.execute(sql, selector)

        self._logger.info(" -- DNS Config 저장")
        if 'dns_config' in template_data:
            sql = """
            INSERT INTO k8s_dns_configs (
                config_id, template_id, nameservers, searches, options
            ) VALUES (
                %(config_id)s, %(template_id)s, %(nameservers)s, %(searches)s, %(options)s
            )
            """
            cursor.execute(sql, template_data['dns_config'])

        self._logger.info(" -- Host Aliases 저장")
        if 'host_aliases' in template_data:
            for alias in template_data['host_aliases']:
                sql = """
                INSERT INTO k8s_host_aliases (
                    alias_id, template_id, ip, hostnames
                ) VALUES (
                    %(alias_id)s, %(template_id)s, %(ip)s, %(hostnames)s
                )
                """
                cursor.execute(sql, alias)

        self._logger.info(" -- Topology Spread Constraints 저장")
        if 'topology_spread_constraints' in template_data:
            for constraint in template_data['topology_spread_constraints']:
                sql = """
                INSERT INTO k8s_topology_spread_constraints (
                    constraint_id, template_id, max_skew, topology_key,
                    when_unsatisfiable, label_selector
                ) VALUES (
                    %(constraint_id)s, %(template_id)s, %(max_skew)s, 
                    %(topology_key)s, %(when_unsatisfiable)s, %(label_selector)s
                )
                """
                cursor.execute(sql, constraint)

    def _insert_node_affinity(self, cursor, node_affinity_data):
        """Node Affinity 규칙 저장"""
        for rule in node_affinity_data['rules']:
            self._logger.info(" -- Node Affinity Rule 저장")
            if rule.get('weight') is None:
                sql = """
                    INSERT INTO k8s_node_affinity_rules (
                        rule_id, template_id, rule_type
                    ) VALUES (
                        %(rule_id)s, %(template_id)s, %(rule_type)s
                    )
                """
                cursor.execute(sql, {
                    'rule_id': rule['rule_id'],
                    'template_id': rule['template_id'],
                    'rule_type': rule['rule_type']
                })
            else:
                sql = """
                            INSERT INTO k8s_node_affinity_rules (
                                rule_id, template_id, rule_type, weight
                            ) VALUES (
                                %(rule_id)s, %(template_id)s, %(rule_type)s, %(weight)s
                            )
                            """
                cursor.execute(sql, rule)

            self._logger.info(" -- Node Selector Terms 저장")
            for term in rule['terms']:
                sql = """
                INSERT INTO k8s_node_selector_terms (
                    term_id, rule_id, term_order
                ) VALUES (
                    %(term_id)s, %(rule_id)s, %(term_order)s
                )
                """
                term_info = {
                    'term_id': term['term_id'],
                    'rule_id': term['rule_id'],
                    'term_order': term['term_order']
                }
                cursor.execute(sql, term_info)

                self._logger.info(" -- Match Expressions 저장")
                for expr in term['expressions']:
                    sql = """
                    INSERT INTO k8s_node_match_expressions (
                        expression_id, term_id, label_key, operator, expression_order
                    ) VALUES (
                        %(expression_id)s, %(term_id)s, %(label_key)s,
                        %(operator)s, %(expression_order)s
                    )
                    """
                    expr_info = {
                        'expression_id': expr['expression_id'],
                        'term_id': expr['term_id'],
                        'label_key': expr['label_key'],
                        'operator': expr['label_key'],
                        'expression_order': expr['expression_order']
                    }
                    cursor.execute(sql, expr_info)

                    self._logger.info(" -- Expression Values 저장")
                    if 'values' in expr:
                        for value in expr['values']:
                            sql = """
                            INSERT INTO k8s_node_match_expression_values (
                                value_id, expression_id, label_value, value_order
                            ) VALUES (
                                %(value_id)s, %(expression_id)s, %(label_value)s,
                                %(value_order)s
                            )
                            """
                            cursor.execute(sql, value)

    def _insert_pod_affinity(self, cursor, pod_affinity_data):
        """Pod Affinity 규칙 저장"""
        for rule in pod_affinity_data['rules']:
            self._logger.info(" -- Pod Affinity Rule 저장")
            sql = """
            INSERT INTO k8s_pod_affinity_rules (
                rule_id, template_id, affinity_type, rule_type,
                weight, topology_key
            ) VALUES (
                %(rule_id)s, %(template_id)s, %(affinity_type)s,
                %(rule_type)s, %(weight)s, %(topology_key)s
            )
            """
            rule_info = {
                'rule_id': rule['rule_id'],
                'template_id': rule['template_id'],
                'affinity_type': rule['affinity_type'],
                'rule_type': rule['rule_type'],
                'weight': rule['weight'],
                'topology_key': rule['topology_key']
            }
            cursor.execute(sql, rule_info)

            self._logger.info(" -- Label Selector 저장")
            if 'label_selector' in rule:
                selector = rule['label_selector']
                sql = """
                INSERT INTO k8s_pod_label_selectors (
                    selector_id, rule_id
                ) VALUES (
                    %(selector_id)s, %(rule_id)s
                )
                """
                selector_info = {
                    'selector_id': selector['selector_id'],
                    'rule_id': selector['rule_id']
                }
                self._logger.info(selector)
                cursor.execute(sql, selector_info)

                self._logger.info(" -- Match Expressions 저장")
                for expr in selector['expressions']:
                    sql = """
                    INSERT INTO k8s_pod_match_expressions (
                        expression_id, selector_id, label_key,
                        operator, expression_order
                    ) VALUES (
                        %(expression_id)s, %(selector_id)s, %(label_key)s,
                        %(operator)s, %(expression_order)s
                    )
                    """
                    expr_info = {
                        'expression_id': expr['expression_id'],
                        'selector_id': expr['selector_id'],
                        'label_key': expr['label_key'],
                        'operator': expr['operator'],
                        'expression_order': expr['expression_order']
                    }
                    cursor.execute(sql, expr_info)

                    self._logger.info(" -- Expression Values 저장")
                    if 'values' in expr:
                        for value in expr['values']:
                            sql = """
                            INSERT INTO k8s_pod_match_expression_values (
                                value_id, expression_id, label_value,
                                value_order
                            ) VALUES (
                                %(value_id)s, %(expression_id)s, %(label_value)s,
                                %(value_order)s
                            )
                            """
                            value_info = {
                                'value_id': value['value_id'],
                                'expression_id': value['expression_id'],
                                'label_value': value['label_value'],
                                'value_order': value['value_order']
                            }
                            cursor.execute(sql, value_info)

            self._logger.info(" -- Namespace Selector 저장")
            if 'namespace_selector' in rule:
                selector = rule['namespace_selector']
                sql = """
                INSERT INTO k8s_namespace_selectors (
                    selector_id, rule_id
                ) VALUES (
                    %(selector_id)s, %(rule_id)s
                )
                """
                selector_info = {
                    'selector_id': selector['selector_id'],
                    'rule_id': selector['rule_id']
                }
                cursor.execute(sql, selector_info)

                self._logger.info(" -- Namespace Match Labels 저장")
                for label in selector['labels']:
                    sql = """
                    INSERT INTO k8s_namespace_match_labels (
                        label_id, selector_id, label_key, label_value
                    ) VALUES (
                        %(label_id)s, %(selector_id)s, %(label_key)s, %(label_value)s
                    )
                    """
                    label_info = {
                        'label_id': label['label_id'],
                        'selector_id': label['selector_id'],
                        'label_key': label['label_key'],
                        'label_value': label['label_value']
                    }
                    cursor.execute(sql, label_info)

    def _insert_security_context(self, cursor, security_context_data):
        """Security Context 저장"""
        security_insert_data = {
            'context_id': security_context_data['context_id'],
            'container_id': security_context_data['container_id'],
            'capabilities_add': security_context_data.get('capabilities_add'),
            'capabilities_drop': security_context_data.get('capabilities_drop'),
            'privileged': self._convert_bool_to_int(security_context_data.get('privileged', False)),
            'run_as_user': security_context_data.get('run_as_user'),
            'run_as_group': security_context_data.get('run_as_group'),
            'run_as_non_root': self._convert_bool_to_int(security_context_data.get('run_as_non_root', False)),
            'read_only_root_filesystem': self._convert_bool_to_int(security_context_data.get('read_only_root_filesystem', False)),
            'allow_privilege_escalation': self._convert_bool_to_int(security_context_data.get('allow_privilege_escalation', False))
        }

        sql = """
        INSERT INTO k8s_security_contexts (
            context_id, container_id, capabilities_add, capabilities_drop,
            privileged, run_as_user, run_as_group, run_as_non_root,
            read_only_root_filesystem, allow_privilege_escalation
        ) VALUES (
            %(context_id)s, %(container_id)s, %(capabilities_add)s,
            %(capabilities_drop)s, %(privileged)s, %(run_as_user)s,
            %(run_as_group)s, %(run_as_non_root)s,
            %(read_only_root_filesystem)s, %(allow_privilege_escalation)s
        )
        """
        cursor.execute(sql, security_insert_data)