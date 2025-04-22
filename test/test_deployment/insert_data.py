#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import pymysql
# import mysql.connector
# from mysql.connector import Error
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class K8sDBManager:
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
			self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
			logger.info(f"Successfully connected to database {database}")
		except Exception as e:
			logger.error(f"Error connecting to database: {e}")
			raise

	def get_connection(self):
		return self.conn




	def insert_application(self, app_name: str, namespace: str, description: str) -> str:
		"""애플리케이션 기본 정보 저장"""
		app_id = self.generate_id("APP", 1)
		try:
			query_string = """
				INSERT INTO k8s_applications (
					app_id, app_name, app_namespace, app_description
				) VALUES ('%s', '%s', '%s', '%s')
			""" %(app_id, app_name, namespace, description)
			self.cursor.execute(query_string)
			# self.conn.commit()
			logger.info(f"Created application with ID: {app_id}")
			return app_id
		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting application: {e}")
			raise

	def insert_metadata(self, deployment_id: str, metadata: Dict[str, Any]) -> None:
		"""메타데이터 저장 (레이블, 어노테이션)"""
		try:
			# 레이블 저장
			if 'labels' in metadata:
				for i, (key, value) in enumerate(metadata['labels'].items(), 1):
					label_id = self.generate_id("LBL", i)
					query_string = """
						INSERT INTO k8s_deployment_labels (
							label_id, deployment_id, label_key, label_value
						) VALUES ('%s', '%s', '%s', '%s')
					""" %(label_id, deployment_id, key, str(value))
					self.cursor.execute(query_string)

			# 어노테이션 저장
			if 'annotations' in metadata:
				for i, (key, value) in enumerate(metadata['annotations'].items(), 1):
					anno_id = self.generate_id("ANN", i)
					query_string = """
						INSERT INTO k8s_deployment_annotations (
							annotation_id, deployment_id, annotation_key, annotation_value
						) VALUES ('%s', '%s', '%s', '%s')
					""" %(anno_id, deployment_id, key, str(value))
					self.cursor.execute(query_string)
		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting metadata: {e}")
			raise

	def insert_node_affinity(self, template_id: str, node_affinity: Dict[str, Any]) -> None:
		"""Node Affinity 설정 저장"""
		try:
			# Required rules
			if 'requiredDuringSchedulingIgnoredDuringExecution' in node_affinity:
				required = node_affinity['requiredDuringSchedulingIgnoredDuringExecution']
				rule_id = self.generate_id("NAR", 1)
				query_string = """
					INSERT INTO k8s_node_affinity_rules (
						rule_id, template_id, rule_type
					) VALUES ('%s', '%s', 'required')
				""" %(rule_id, template_id)
				self.cursor.execute(query_string)

				for term_idx, term in enumerate(required['nodeSelectorTerms'], 1):
					term_id = self.generate_id("NST", term_idx)
					query_string = """
						INSERT INTO k8s_node_selector_terms (
							term_id, rule_id, term_order
						) VALUES ('%s', '%s', %d)
					""" %(term_id, rule_id, term_idx)
					print("term_id:", term_id)
					print(query_string)
					self.cursor.execute(query_string)

					self.insert_node_match_expressions(term_id, term.get('matchExpressions', []))

			# Preferred rules
			if 'preferredDuringSchedulingIgnoredDuringExecution' in node_affinity:
				for pref_idx, pref in enumerate(node_affinity['preferredDuringSchedulingIgnoredDuringExecution'], 1):
					rule_id = self.generate_id("NAR", pref_idx + 100)
					query_string = """
						INSERT INTO k8s_node_affinity_rules (
							rule_id, template_id, rule_type, preference_weight
						) VALUES ('%s', '%s', 'preferred', '%s')
					""" %(rule_id, template_id, pref['weight'])
					self.cursor.execute(query_string)

					term_id = self.generate_id("NST", pref_idx + 100)
					query_string = """
						INSERT INTO k8s_node_selector_terms (
							term_id, rule_id, term_order
						) VALUES ('%s', '%s', %d)
					""" %(term_id, rule_id, 1)
					print("term_id:", term_id)
					print(query_string)
					self.cursor.execute(query_string)

					self.insert_node_match_expressions(term_id, pref['preference'].get('matchExpressions', []))

		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting node affinity: {e}")
			raise

	def insert_node_match_expressions(self, term_id: str, expressions: List[Dict[str, Any]]) -> None:
		print("=== Termid: ", term_id)
		"""Match Expressions 저장"""
		try:
			for expr_idx, expr in enumerate(expressions, 1):
				expr_id = self.generate_id("EXP", expr_idx)
				query_string = """
					INSERT INTO k8s_node_match_expressions (
						expression_id, term_id, label_key, operator, expression_order
					) VALUES ('%s', '%s', '%s', '%s', %d)
				""" %(expr_id, term_id, expr['key'], expr['operator'], expr_idx)
				print(query_string)
				self.cursor.execute(query_string)

				if 'values' in expr:
					for val_idx, value in enumerate(expr['values'], 1):
						val_id = self.generate_id("VAL", val_idx)
						query_string = """
							INSERT INTO k8s_node_match_expression_values (
								value_id, expression_id, label_value, value_order
							) VALUES ('%s', '%s', '%s', %d)
						""" %(val_id, expr_id, value, val_idx)
						self.cursor.execute(query_string)
		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting match expressions: {e}")
			raise

	def insert_pod_affinity(self, template_id: str, affinity_data: Dict[str, Any], affinity_type: str) -> None:
		"""Pod Affinity/Anti-Affinity 설정 저장"""
		try:
			# Required rules
			if 'requiredDuringSchedulingIgnoredDuringExecution' in affinity_data:
				for req_idx, required in enumerate(
						affinity_data['requiredDuringSchedulingIgnoredDuringExecution'], 1):
					rule_id = self.generate_id("PAR", req_idx)
					self.insert_pod_affinity_rule(template_id, rule_id, affinity_type, 'required', required, None)

			# Preferred rules
			if 'preferredDuringSchedulingIgnoredDuringExecution' in affinity_data:
				for pref_idx, preferred in enumerate(affinity_data['preferredDuringSchedulingIgnoredDuringExecution'], 1):
					rule_id = self.generate_id("PAR", pref_idx + 100)
					self.insert_pod_affinity_rule(template_id, rule_id, affinity_type, 'preferred', preferred.get('podAffinityTerm', {}), preferred.get('weight'))

		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting pod affinity: {e}")
			raise

	def insert_pod_affinity_rule(self, template_id: str, rule_id: str, affinity_type: str, rule_type: str, term_data: Dict[str, Any], weight: Optional[int]) -> None:
		"""Pod Affinity Rule 저장"""
		try:
			if weight:
				query_string = """
					INSERT INTO k8s_pod_affinity_rules (
						rule_id, template_id, affinity_type, rule_type, weight
					) VALUES ('%s', '%s', '%s', '%s', %d)
				""" %(rule_id, template_id, affinity_type, rule_type, weight)
			else:
				query_string = """
						INSERT INTO k8s_pod_affinity_rules (
							rule_id, template_id, affinity_type, rule_type
						) VALUES ('%s', '%s', '%s', '%s')
				""" % (rule_id, template_id, affinity_type, rule_type)
			self.cursor.execute(query_string)

			term_id = self.generate_id("PAT", int(rule_id.split('_')[-1]))
			query_string = """
				INSERT INTO k8s_pod_affinity_terms (
					term_id, rule_id, topology_key, term_order
				) VALUES ('%s', '%s', '%s', '%s')
			""" %(term_id, rule_id, term_data.get('topologyKey'), 1)
			self.cursor.execute(query_string)

			if 'labelSelector' in term_data:
				self.insert_pod_label_selector(term_id, term_data['labelSelector'])

			if 'namespaceSelector' in term_data:
				self.insert_namespace_selector(term_id, term_data['namespaceSelector'])

		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting pod affinity rule: {e}")
			raise

	def insert_pod_label_selector(self, term_id: str, selector_data: Dict[str, Any]) -> None:
		"""Pod Label Selector 저장"""
		try:
			selector_id = self.generate_id("SEL", int(term_id.split('_')[-1]))
			print("+++ term: ", term_id)
			query_string = """
				INSERT INTO k8s_pod_label_selectors (selector_id, term_id)
				VALUES ('%s', '%s')
			""" % (selector_id, term_id)
			self.cursor.execute(query_string)

			if 'matchExpressions' in selector_data:
				self.insert_pod_match_expressions(selector_id, selector_data['matchExpressions'])

		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting pod label selector: {e}")
			raise

	def insert_pod_match_expressions(self, selector_id: str, expressions: List[Dict[str, Any]]) -> None:
		print("=== selector_id: ", selector_id)
		"""Match Expressions 저장"""
		try:
			for expr_idx, expr in enumerate(expressions, 1):
				expr_id = self.generate_id("EXP", expr_idx)
				query_string = """
					INSERT INTO k8s_pod_match_expressions (
						expression_id, selector_id, label_key, operator, expression_order
					) VALUES ('%s', '%s', '%s', '%s', %d)
				""" %(expr_id, selector_id, expr['key'], expr['operator'], expr_idx)
				print(query_string)
				self.cursor.execute(query_string)


				if 'values' in expr:
					for val_idx, value in enumerate(expr['values'], 1):
						val_id = self.generate_id("VAL", val_idx)
						query_string = """
							INSERT INTO k8s_pod_match_expression_values (
								value_id, expression_id, label_value, value_order
							) VALUES ('%s', '%s', '%s', %d)
						""" %(val_id, expr_id, value, val_idx)
						self.cursor.execute(query_string)
		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting match expressions: {e}")
			raise

	def insert_namespace_selector(self, term_id: str, selector_data: Dict[str, Any]) -> None:
		"""Namespace Selector 저장"""
		try:
			selector_id = self.generate_id("NSS", int(term_id.split('_')[-1]))
			query_string = """
				INSERT INTO k8s_namespace_selectors (selector_id, term_id)
				VALUES ('%s', '%s')
			""" %(selector_id, term_id)
			self.cursor.execute(query_string)

			if 'matchLabels' in selector_data:
				for idx, (key, value) in enumerate(selector_data['matchLabels'].items(), 1):
					label_id = self.generate_id("NSL", idx)
					query_string = """
						INSERT INTO k8s_namespace_match_labels (
							label_id, selector_id, label_key, label_value
						) VALUES ('%s', '%s', '%s', '%s')
					""" %(label_id, selector_id, key, value)
					self.cursor.execute(query_string)

		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting namespace selector: {e}")
			raise

	def insert_container(self, template_id: str, container_data: Dict[str, Any]) -> str:
		"""컨테이너 정보 저장"""
		try:
			container_id = self.generate_id("CNT", 1)
			image_parts = container_data['image'].split(':')
			image_name = image_parts[0]
			image_tag = image_parts[1] if len(image_parts) > 1 else 'latest'

			query_string = """
				INSERT INTO k8s_containers (
					container_id, template_id, container_name, 
					image_name, image_tag, image_pull_policy
				) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')
			""" %(container_id, template_id, container_data['name'], image_name, image_tag, container_data.get('imagePullPolicy', 'IfNotPresent'))
			self.cursor.execute(query_string)

			# Resources
			if 'resources' in container_data:
				self.insert_container_resources(container_id, container_data['resources'])

			# Ports
			if 'ports' in container_data:
				self.insert_container_ports(container_id, container_data['ports'])

			# Environment Variables
			if 'env' in container_data:
				self.insert_container_env_vars(container_id, container_data['env'])

			return container_id

		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting container: {e}")
			raise

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
					resource_info.get('requests')  if resource_info.get('requests') else None,
					resource_info.get('limits') if resource_info.get('limits') else None
				))

			if values:
				query = """
					INSERT INTO k8s_container_resources (
						resource_id, container_id, resource_category,
						resource_name, request_amount, limit_amount
					) VALUES (%s, %s, %s, %s, %s, %s)
				"""
				self.cursor.executemany(query, values)
				self.conn.commit()

		except Exception as e:
			self.conn.rollback()
			logger.error(f"Error inserting container resources: {e}")
			raise

		logger.info(f"Successfully inserted resources for container: {container_id}")

	def insert_container_ports(self, container_id: str, ports: List[Dict[str, Any]]) -> None:
		"""컨테이너 포트 설정 저장"""
		try:
			for idx, port in enumerate(ports, 1):
				port_id = self.generate_id("PRT", idx)
				query_string = """
					INSERT INTO k8s_container_ports (
						port_id, container_id, port_name,
						container_port, protocol
					) VALUES ('%s', '%s', '%s', '%s', '%s')
				""" %(
					port_id, container_id,
					port.get('name'),
					port['containerPort'],
					port.get('protocol', 'TCP')
				)
				self.cursor.execute(query_string)
		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting container ports: {e}")
			raise

	def insert_container_env_vars(self, container_id: str, env_vars: List[Dict[str, Any]]) -> None:
		"""컨테이너 환경변수 설정 저장"""
		try:
			for idx, env in enumerate(env_vars, 1):
				env_id = self.generate_id("ENV", idx)

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
					else:
						continue

				print(value_reference)
				query_string = """
					INSERT INTO k8s_env_variables (
						env_id, container_id, env_name,
						env_value_type, value_reference
					) VALUES ('%s', '%s', '%s', '%s', %s)
				""" %(
					env_id, container_id,
					env['name'], value_type,
					json.dumps(value_reference)
				)
				print(query_string)
				self.cursor.execute(query_string)
		except Exception as e:
			# self.conn.rollback()
			logger.error(f"Error inserting container environment variables: {e}")
			raise

	def insert_deployment(self, app_id: str, deployment_data: Dict[str, Any]) -> str:
		"""Deployment 전체 정보 저장"""
		try:
			# 1. Deployment 기본 정보
			deployment_id = self.generate_id("DEP", 1)
			print(deployment_id)
			query_string = """
				INSERT INTO k8s_deployments (
					deployment_id, app_id, deployment_name,
					deployment_namespace, replica_count
				) VALUES ('%s', '%s', '%s', '%s', %d)
			""" %(
				deployment_id, app_id,
				deployment_data['metadata']['name'],
				deployment_data['metadata']['namespace'],
				deployment_data['spec']['replicas']
			)
			self.cursor.execute(query_string)

			# 2. 메타데이터 (레이블, 어노테이션)
			print("# 2. 메타데이터 (레이블, 어노테이션)")
			self.insert_metadata(deployment_id, deployment_data['metadata'])

			# 3. Selector
			if 'selector' in deployment_data['spec']:
				for key, value in deployment_data['spec']['selector'].get('matchLabels', {}).items():
					selector_id = self.generate_id("SEL", 1)
					query_string = """
						INSERT INTO k8s_deployment_selectors (
							selector_id, deployment_id, label_key, label_value
						) VALUES ('%s', '%s', '%s', '%s')
					""" %(selector_id, deployment_id, key, value)
					self.cursor.execute(query_string)

			# 4. Pod Template
			template_id = self.generate_id("TPL", 1)
			query_string = """
				INSERT INTO k8s_pod_templates (template_id, deployment_id)
				VALUES ('%s', '%s')
			""" %(template_id, deployment_id)
			self.cursor.execute(query_string)

			# 5. Pod Template 메타데이터
			pod_metadata = deployment_data['spec']['template']['metadata']
			if 'labels' in pod_metadata:
				for key, value in pod_metadata['labels'].items():
					label_id = self.generate_id("PLBL", 1)
					query_string = """
						INSERT INTO k8s_pod_template_labels (
							label_id, template_id, label_key, label_value
						) VALUES ('%s', '%s', '%s', '%s')
					""" %(label_id, template_id, key, value)
					print(query_string)
					self.cursor.execute(query_string)

			# 6. Affinity 설정
			if 'affinity' in deployment_data['spec']['template']['spec']:
				affinity_data = deployment_data['spec']['template']['spec']['affinity']

				if 'nodeAffinity' in affinity_data:
					self.insert_node_affinity(template_id, affinity_data['nodeAffinity'])

				if 'podAffinity' in affinity_data:
					self.insert_pod_affinity(template_id, affinity_data['podAffinity'], 'affinity')

				if 'podAntiAffinity' in affinity_data:
					self.insert_pod_affinity(template_id, affinity_data['podAntiAffinity'], 'anti-affinity')

			# 7. 컨테이너
			for container in deployment_data['spec']['template']['spec']['containers']:
				self.insert_container(template_id, container)

			self.conn.commit()
			logger.info(f"Successfully inserted deployment with ID: {deployment_id}")
			return deployment_id

		except Exception as e:
			# self.conn.rollback()
			print("-----------")
			logger.error(f"Error inserting deployment: {e}")
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
	# 데이터베이스 연결 설정
	db_config = {
		'host': '127.0.0.1',
		'port': 13306,
		'user': 'kasugare',
		'password': 'uncsbjsa',
		'database': 'serving_test_1'
	}
	# DB 매니저 초기화
	db_manager = K8sDBManager(**db_config)
	conn = db_manager.get_connection()

	# YAML 파일 경로
	yaml_file = 'deployment.yaml'

	try:
		# YAML 파일 읽기
		with open(yaml_file, 'r') as f:
			deployment_data = yaml.safe_load(f)

		# 애플리케이션 등록
		app_id = db_manager.insert_application(
			app_name='AI_Serving_Test_20',
			namespace=deployment_data['metadata']['namespace'],
			description='AI Model Serving Application with GPU Support'
		)

		# Deployment 등록
		deployment_id = db_manager.insert_deployment(app_id, deployment_data)

		logger.info(f"Successfully processed deployment.yaml")
		logger.info(f"Application ID: {app_id}")
		logger.info(f"Deployment ID: {deployment_id}")
		conn.commit()

	except Exception as e:
		logger.error(f"Error processing YAML file: {e}")
		conn.rollback()
		raise
	finally:
		db_manager.close()

if __name__ == "__main__":
	main()


# self._insert_pod_template
# self._insert_node_affinity
# self._insert_pod_affinity
# self._insert_security_context