#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import pymysql
# import mysql.connector
# from mysql.connector import Error
import logging
from typing import Dict, Any, List, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class K8sDBReader:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        try:
            self.conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            self.cursor = self.conn.cursor()
            logger.info(f"Successfully connected to database {database}")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def get_deployment(self, deployment_name: str, namespace: str) -> Dict[str, Any]:
        """deployment 정보 조회 및 YAML 구조로 변환"""
        print(" ** deployment 정보 조회 및 YAML 구조로 변환  ** ")
        try:
            print(" Step 1. Deployment 기본 정보 조회")
            query_string = """
				SELECT * FROM k8s_deployments 
				WHERE deployment_name = '%s' AND deployment_namespace = '%s'
			""" %(deployment_name, namespace)
            self.cursor.execute(query_string)
            deployment = self.cursor.fetchone()

            if not deployment:
                raise ValueError(f"Deployment {deployment_name} not found in namespace {namespace}")
            deployment_id = deployment['deployment_id']
            # 2. YAML 구조 생성
            yaml_dict = {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': self.get_metadata(deployment_id),
                'spec': self.get_deployment_spec(deployment_id, deployment['replica_count'])
            }
            return yaml_dict

        except Exception as e:
            logger.error(f"Error fetching deployment: {e}")
            raise

    def get_metadata(self, deployment_id: str) -> Dict[str, Any]:
        print(" # Step 2: 메타데이터 정보 조회")
        """메타데이터 정보 조회"""
        try:
            print("  - 기본 정보 조회")
            query_string = """
				SELECT deployment_name as name, deployment_namespace as namespace 
				FROM k8s_deployments WHERE deployment_id = '%s'
			""" %(deployment_id)
            self.cursor.execute(query_string)
            metadata = self.cursor.fetchone()

            print("  - 레이블 조회")
            query_string = """
                SELECT label_key, label_value FROM k8s_deployment_labels 
				WHERE deployment_id = '%s'
			""" %(deployment_id)
            self.cursor.execute(query_string)
            labels = {row['label_key']: row['label_value'] for row in self.cursor.fetchall()}

            print("  - 어노테이션 조회")
            query_string = """
                SELECT annotation_key, annotation_value FROM k8s_deployment_annotations 
				WHERE deployment_id = '%s'
            			""" % (deployment_id)
            self.cursor.execute(query_string)
            annotations = {row['annotation_key']: row['annotation_value'] for row in self.cursor.fetchall()}
            metadata.update({
                'labels': labels,
                'annotations': annotations
            })

            return metadata

        except Exception as e:
            logger.error(f"Error fetching metadata: {e}")
            raise

    def get_deployment_spec(self, deployment_id: str, replicas: int) -> Dict[str, Any]:
        """Deployment Spec 정보 조회"""
        print(" # Step 3: Deployment Spec 정보 조회")
        try:
            print("  - Selector 조회")
            query_string = """
                SELECT label_key, label_value FROM k8s_deployment_selectors 
                WHERE deployment_id = '%s'
            """ %deployment_id
            self.cursor.execute(query_string)
            selector = {row['label_key']: row['label_value'] for row in self.cursor.fetchall()}

            print("  - Template 정보 조회")
            template = self.get_pod_template(deployment_id)
            result = {
                'replicas': replicas,
                'selector': {
                    'matchLabels': selector
                },
                'template': template
            }

            return result

        except Exception as e:
            logger.error(f"Error fetching deployment spec: {e}")
            raise

    def get_pod_template(self, deployment_id: str) -> Dict[str, Any]:
        """Pod Template 정보 조회"""
        print(" # Step 3: Pod Template 정보 조회")

        try:
            print("  - Template ID 조회")
            query_string = """
                SELECT template_id FROM k8s_pod_templates 
				WHERE deployment_id = '%s'
            """ % (deployment_id)
            self.cursor.execute(query_string)
            template = self.cursor.fetchone()
            template_id = template['template_id']

            # Template Labels 조회
            print("  - Template Labels 조회")
            query_string = """
                SELECT label_key, label_value FROM k8s_pod_template_labels 
				WHERE template_id = '%s'
            """ % (template_id)
            self.cursor.execute(query_string)
            labels = {row['label_key']: row['label_value'] for row in self.cursor.fetchall()}

            # Template Spec 조회
            print("  - Template Spec 조회")
            spec = {
                'affinity': self.get_affinity(template_id),
                'containers': self.get_containers(template_id)
            }

            return {
                'metadata': {
                    'labels': labels
                },
                'spec': spec
            }

        except Exception as e:
            logger.error(f"Error fetching pod template: {e}")
            raise

    def get_affinity(self, template_id: str) -> Dict[str, Any]:
        """Affinity 정보 조회"""
        print(" # Step 4: Affinity 정보 조회")
        try:
            affinity = {}

            # Node Affinity
            print("  - Node Affinity")
            node_affinity = self.get_node_affinity(template_id)
            if node_affinity:
                affinity['nodeAffinity'] = node_affinity

            # Pod Affinity
            print("  - Pod Affinity")
            pod_affinity = self.get_pod_affinity(template_id, 'affinity')
            if pod_affinity:
                affinity['podAffinity'] = pod_affinity

            # Pod Anti-Affinity
            print("  - Pod Anti-Affinity")
            pod_anti_affinity = self.get_pod_affinity(template_id, 'anti-affinity')
            if pod_anti_affinity:
                affinity['podAntiAffinity'] = pod_anti_affinity

            return affinity

        except Exception as e:
            logger.error(f"Error fetching affinity: {e}")
            raise

    def get_pod_affinity(self, template_id: str, affinity_type: str) -> Dict[str, Any]:
        """Pod Affinity/Anti-Affinity 정보 조회"""
        try:
            affinity_dict = {}

            # Required 규칙 조회
            required_rules = self.get_pod_affinity_rules(template_id, affinity_type, 'required')
            if required_rules:
                affinity_dict['requiredDuringSchedulingIgnoredDuringExecution'] = required_rules

            # Preferred 규칙 조회
            preferred_rules = self.get_pod_affinity_rules(template_id, affinity_type, 'preferred')
            if preferred_rules:
                affinity_dict['preferredDuringSchedulingIgnoredDuringExecution'] = preferred_rules

            return affinity_dict if affinity_dict else None

        except Exception as e:
            logger.error(f"Error fetching pod {affinity_type}: {e}")
            raise

    def get_pod_affinity_rules(self, template_id: str, affinity_type: str, rule_type: str) -> List[Dict[str, Any]]:
        """Pod Affinity/Anti-Affinity 규칙 조회"""
        try:
            # 규칙 기본 정보 조회
            query_string = """
                SELECT rule_id, weight 
                FROM k8s_pod_affinity_rules 
                WHERE template_id = '%s' 
                AND affinity_type = '%s' 
                AND rule_type = '%s' 
                ORDER BY rule_id
            """ %(template_id, affinity_type, rule_type)
            print(query_string)
            self.cursor.execute(query_string)
            rules = self.cursor.fetchall()

            rules_list = []
            for rule in rules:
                # Term 정보 조회
                terms = self.get_pod_affinity_terms(rule['rule_id'])

                if rule_type == 'required':
                    # Required 규칙은 terms를 직접 리스트에 추가
                    rules_list.extend(terms)
                else:
                    # Preferred 규칙은 weight와 함께 포함
                    for term in terms:
                        rules_list.append({
                            'weight': rule['weight'],
                            'podAffinityTerm': term
                        })

            return rules_list

        except Exception as e:
            logger.error(f"Error fetching pod affinity rules: {e}")
            raise

    def get_pod_affinity_terms(self, rule_id: str) -> List[Dict[str, Any]]:
        """Pod Affinity Terms 조회"""
        print(" - Step xx: Pod Affinity Terms 조회")
        try:
            query_string = """
                SELECT term_id, topology_key 
                FROM k8s_pod_affinity_terms 
                WHERE rule_id = '%s' 
                ORDER BY term_order
            """ %rule_id
            self.cursor.execute(query_string)
            terms = self.cursor.fetchall()

            terms_list = []
            for term in terms:
                term_dict = {'topologyKey': term['topology_key']}

                # Label Selector 조회
                label_selector = self.get_pod_label_selector(term['term_id'])
                if label_selector:
                    term_dict['labelSelector'] = label_selector

                # Namespace Selector 조회
                namespace_selector = self.get_namespace_selector(term['term_id'])
                if namespace_selector:
                    term_dict['namespaceSelector'] = namespace_selector

                terms_list.append(term_dict)

            return terms_list

        except Exception as e:
            logger.error(f"Error fetching pod affinity terms: {e}")
            raise

    def get_pod_label_selector(self, term_id: str) -> Dict[str, Any]:
        """Pod Label Selector 조회"""
        print(" - Step xx: Pod Label Selector 조회")
        try:
            query_string = """
                SELECT selector_id 
                FROM k8s_pod_label_selectors 
                WHERE term_id = '%s'
            """ %term_id
            self.cursor.execute(query_string)
            selector = self.cursor.fetchone()

            if selector:
                selector_dict = {}

                # Match Expressions 조회
                print("  - Match Expressions 조회")
                expressions = self.get_pod_match_expressions(selector['selector_id'])
                if expressions:
                    selector_dict['matchExpressions'] = expressions

                return selector_dict if selector_dict else None

            return None

        except Exception as e:
            logger.error(f"Error fetching pod label selector: {e}")
            raise

    def get_pod_match_expressions(self, selector_id: str) -> List[Dict[str, Any]]:
        """Pod Match Expressions 조회"""
        print(" - Step xx: Pod Match Expressions 조회")
        try:
            query_string = """
                SELECT expression_id, label_key, operator as operator 
                FROM k8s_pod_match_expressions 
                WHERE selector_id = '%s' 
                ORDER BY expression_order
            """ %selector_id
            self.cursor.execute(query_string)
            expressions = self.cursor.fetchall()

            expressions_list = []
            for expr in expressions:
                expression = {
                    'key': expr['label_key'],
                    'operator': expr['operator']
                }

                # Values 조회 (Exists/DoesNotExist 연산자는 values가 없음)
                print("  - Values 조회 (Exists/DoesNotExist 연산자는 values가 없음)")
                if expr['operator'] not in ['Exists', 'DoesNotExist']:
                    query_string = """
                    SELECT label_value 
                        FROM k8s_pod_match_expression_values 
                        WHERE expression_id = '%s' 
                        ORDER BY value_order
                    """ %expr['expression_id']
                    self.cursor.execute(query_string)
                    values = [row['label_value'] for row in self.cursor.fetchall()]
                    if values:
                        expression['values'] = values

                expressions_list.append(expression)

            return expressions_list

        except Exception as e:
            logger.error(f"Error fetching pod match expressions: {e}")
            raise

    def get_namespace_selector(self, term_id: str) -> Dict[str, Any]:
        """Namespace Selector 조회"""
        print(" - Step xx: Namespace Selector 조회")
        try:
            query_string = """
                SELECT selector_id 
                FROM k8s_namespace_selectors 
                WHERE term_id = '%s'
            """ %term_id
            print(query_string)
            self.cursor.execute(query_string)
            selector = self.cursor.fetchone()

            if selector:
                # Match Labels 조회
                print("  - Match Labels 조회")
                query_string = """
                    SELECT label_key, label_value 
                    FROM k8s_namespace_match_labels 
                    WHERE selector_id = '%s'
                """ %selector['selector_id']
                self.cursor.execute(query_string)
                labels = self.cursor.fetchall()

                if labels:
                    return {
                        'matchLabels': {
                            label['label_key']: label['label_value']
                            for label in labels
                        }
                    }

            return None

        except Exception as e:
            logger.error(f"Error fetching namespace selector: {e}")
            raise

    def get_node_affinity(self, template_id: str) -> Dict[str, Any]:
        """Node Affinity 정보 조회"""
        print(" # Step 5: Node Affinity 정보 조회")
        node_affinity = {}

        # Required 규칙 조회
        print("  - Required 규칙 조회")
        required_rules = self.get_node_affinity_rules(template_id, 'required')
        print(required_rules)
        if required_rules:
            node_affinity['requiredDuringSchedulingIgnoredDuringExecution'] = {
                'nodeSelectorTerms': required_rules
            }

        # Preferred 규칙 조회
        print("  - Preferred 규칙 조회")
        preferred_rules = self.get_node_affinity_rules(template_id, 'preferred')
        if preferred_rules:
            node_affinity['preferredDuringSchedulingIgnoredDuringExecution'] = preferred_rules

        return node_affinity

    def get_node_affinity_rules(self, template_id: str, rule_type: str) -> List[Dict[str, Any]]:
        """Node Affinity 규칙 조회"""
        print(" # Step 6: Node Affinity 규칙 조회")
        try:
            if rule_type == 'required':
                # Required 규칙의 nodeSelectorTerms 조회
                print("  - Required 규칙의 nodeSelectorTerms 조회")
                return self.get_node_selector_terms(template_id)
            else:
                # Preferred 규칙 조회
                print("  - Preferred 규칙 조회")
                query_string = """
                    SELECT rule_id, weight as weight 
					FROM k8s_node_affinity_rules 
					WHERE template_id = '%s' AND rule_type = 'preferred'
					ORDER BY rule_id
                """ % (template_id)
                self.cursor.execute(query_string)
                rules = self.cursor.fetchall()

                preferred_rules = []
                for rule in rules:
                    expressions = self.get_match_expressions(rule['rule_id'])
                    if expressions:
                        preferred_rules.append({
                            'weight': rule['weight'],
                            'preference': {
                                'matchExpressions': expressions
                            }
                        })

                return preferred_rules

        except Exception as e:
            logger.error(f"Error fetching node affinity rules: {e}")
            raise

    def get_node_selector_terms(self, template_id: str) -> List[Dict[str, Any]]:
        """Node Selector Terms 조회"""
        print(" # Step 7: Node Selector Terms 조회")
        try:
            query_string = """
				SELECT term_id 
				FROM k8s_node_selector_terms nst
				JOIN k8s_node_affinity_rules nar ON nst.rule_id = nar.rule_id
				WHERE nar.template_id = '%s' AND nar.rule_type = 'required'
				ORDER BY term_id
			""" %template_id
            self.cursor.execute(query_string)
            terms = self.cursor.fetchall()

            selector_terms = []
            for term in terms:
                expressions = self.get_match_expressions(term['term_id'])
                if expressions:
                    selector_terms.append({
                        'matchExpressions': expressions
                    })

            return selector_terms

        except Exception as e:
            logger.error(f"Error fetching node selector terms: {e}")
            raise

    def get_match_expressions(self, term_id: str) -> List[Dict[str, Any]]:
        """Match Expressions 조회"""
        print(" # Step 8: Match Expressions 조회")
        try:
            query_string = """
				SELECT expression_id, label_key, operator as operator
				FROM k8s_node_match_expressions
				WHERE term_id = '%s'
				ORDER BY expression_order
			""" %term_id
            self.cursor.execute(query_string)
            expressions = self.cursor.fetchall()

            match_expressions = []
            for expr in expressions:
                expression = {
                    'key': expr['label_key'],
                    'operator': expr['operator']
                }

                # Values 조회 (Exists/DoesNotExist 연산자는 values가 없음)
                print("  - Values 조회 (Exists/DoesNotExist 연산자는 values가 없음)")
                if expr['operator'] not in ['Exists', 'DoesNotExist']:
                    query_string = """
						SELECT label_value 
						FROM k8s_node_match_expression_values
						WHERE expression_id = '%s'
						ORDER BY value_order
					""" %expr['expression_id']
                    self.cursor.execute(query_string)
                    values = [row['label_value'] for row in self.cursor.fetchall()]
                    if values:
                        expression['values'] = values

                match_expressions.append(expression)

            return match_expressions

        except Exception as e:
            logger.error(f"Error fetching match expressions: {e}")
            raise

    def get_containers(self, template_id: str) -> List[Dict[str, Any]]:
        """Container 정보 조회"""
        try:
            query_string = """
				SELECT * FROM k8s_containers 
				WHERE template_id = '%s'
			""" %template_id
            self.cursor.execute(query_string)
            containers = self.cursor.fetchall()

            container_specs = []
            for container in containers:
                container_id = container['container_id']

                # 기본 컨테이너 정보
                container_spec = {
                    'name': container['container_name'],
                    'image': f"{container['image_name']}:{container['image_tag']}"
                }

                # Resources
                resources = self.get_container_resources(container_id)
                if resources:
                    container_spec['resources'] = resources

                # Ports
                ports = self.get_container_ports(container_id)
                if ports:
                    container_spec['ports'] = ports

                # Environment Variables
                env = self.get_container_env_vars(container_id)
                if env:
                    container_spec['env'] = env

                container_specs.append(container_spec)

            return container_specs

        except Exception as e:
            logger.error(f"Error fetching containers: {e}")
            raise

    def get_container_resources(self, container_id: str) -> Dict[str, Any]:
        """Container Resources 조회"""
        try:
            query_string = """
				SELECT resource_name, request_amount, limit_amount
				FROM k8s_container_resources
				WHERE container_id = '%s'
			""" %container_id
            self.cursor.execute(query_string)
            resources = self.cursor.fetchall()

            resource_spec = {'requests': {}, 'limits': {}}
            for resource in resources:
                if resource['request_amount']:
                    resource_spec['requests'][resource['resource_name']] = resource['request_amount']
                if resource['limit_amount']:
                    resource_spec['limits'][resource['resource_name']] = resource['limit_amount']

            return resource_spec if resource_spec['requests'] or resource_spec['limits'] else None

        except Exception as e:
            logger.error(f"Error fetching container resources: {e}")
            raise

    def get_container_ports(self, container_id: str) -> List[Dict[str, Any]]:
        """Container Ports 조회"""
        try:
            query_string = """
				SELECT port_name, container_port, protocol
				FROM k8s_container_ports
				WHERE container_id = '%s'
				ORDER BY port_id
			""" %container_id
            self.cursor.execute(query_string)
            ports = self.cursor.fetchall()

            return [{
                'name': port['port_name'],
                'containerPort': port['container_port'],
                'protocol': port['protocol']
            } for port in ports]

        except Exception as e:
            logger.error(f"Error fetching container ports: {e}")
            raise

    def get_container_env_vars(self, container_id: str) -> List[Dict[str, Any]]:
        """Container Environment Variables 조회"""
        try:
            query_string = """
				SELECT env_name, env_value_type, value_reference
				FROM k8s_env_variables
				WHERE container_id = '%s'
				ORDER BY env_id
			""" %container_id
            self.cursor.execute(query_string)
            env_vars = self.cursor.fetchall()

            env_list = []
            for env in env_vars:
                env_var = {'name': env['env_name']}

                if env['env_value_type'] == 'PLAIN':
                    value_ref = json.loads(env['value_reference'])
                    env_var['value'] = value_ref['value']
                else:
                    value_ref = json.loads(env['value_reference'])
                    if env['env_value_type'] == 'FIELD_REF':
                        env_var['valueFrom'] = {'fieldRef': {'fieldPath': value_ref['fieldPath']}}
                    elif env['env_value_type'] == 'SECRET':
                        env_var['valueFrom'] = {'secretKeyRef': value_ref}
                    elif env['env_value_type'] == 'CONFIG_MAP':
                        env_var['valueFrom'] = {'configMapKeyRef': value_ref}

                env_list.append(env_var)

            return env_list

        except Exception as e:
            logger.error(f"Error fetching container environment variables: {e}")
            raise

    def close(self):
        """데이터베이스 연결 종료"""
        try:
            self.cursor.close()
            self.conn.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")


def main():
    """메인 실행 함수"""
    db_config = {
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'kasugare',
        'password': 'uncsbjsa',
        'database': 'serving_test_1'
    }

    try:
        # DB 리더 초기화
        db_reader = K8sDBReader(**db_config)

        # Deployment 정보 조회
        deployment_yaml = db_reader.get_deployment(
            deployment_name='complete-affinity-demo-7',
            namespace='affinity-demo-7'
            # deployment_name = 'complete-affinity-demo',
            # namespace = 'affinity-demo'
        )

        # YAML 파일로 저장
        output_file = 'deployment_from_db.yaml'
        with open(output_file, 'w') as f:
            yaml.dump(deployment_yaml, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Successfully generated deployment YAML: {output_file}")

    except Exception as e:
        logger.error(f"Error generating deployment YAML: {e}")
        raise
    finally:
        db_reader.close()

if __name__ == "__main__":
    main()