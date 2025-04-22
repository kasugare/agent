
from deployment_service import DeploymentService
from deployment_transform import DeploymentTransformer
from deployment_access import DeploymentAccess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# main.py
def main(deployment_file_name):
    # DB 설정
    db_config = {
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'kasugare',
        'password': 'uncsbjsa',
        'database': 'serving_test_2'
    }

    # 컴포넌트 초기화
    access = DeploymentAccess(logger, db_config)
    transformer = DeploymentTransformer(logger)
    service = DeploymentService(logger, transformer, access)

    # YAML 파일 읽기
    with open(deployment_file_name, 'r') as file:
        yaml_content = file.read()

    # Deployment 생성
    # try:
    deployment_id = service.create_deployment(yaml_content)
    print(f"Successfully created deployment with ID: {deployment_id}")
    # except Exception as e:
        # print(f"Failed to create deployment: {str(e)}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        input_file = 'deployment.yaml'
    else:
        input_file = sys.argv[1]

    main(input_file)