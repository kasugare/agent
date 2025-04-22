
import yaml


class DeploymentService:
    def __init__(self, logger, transformer, access):
        self._logger = logger
        self.transformer = transformer
        self.access = access

    def create_deployment(self, yaml_content: str) -> str:
        """
        Deployment YAML을 파싱하고 DB에 저장
        """
        try:
            # YAML을 파이썬 딕셔너리로 변환
            deployment_dict = yaml.safe_load(yaml_content)

            # 데이터 변환
            transformed_data = self.transformer.transform_deployment(deployment_dict)

            # DB 저장
            deployment_id = self.access.insert_deployment(transformed_data)

            return deployment_id
        except Exception as e:
            raise Exception(f"Failed to create deployment: {str(e)}")


