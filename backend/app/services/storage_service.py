import os
import tempfile
import boto3
from botocore.client import Config
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.bucket_name = settings.S3_BUCKET

    def generate_presigned_upload_url(
        self,
        object_name: str,
        content_type: str,
        expiration: int = 3600,  # 1 час
    ) -> str:
        """
        Генерирует presigned URL для прямой загрузки файла (PUT) во фронтенде.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_name,
                    "ContentType": content_type,
                },
                ExpiresIn=expiration,
            )
            logger.info("presigned_upload_url_generated", object_name=object_name)
            return url
        except Exception as e:
            logger.error("presigned_url_generation_failed", error=str(e))
            raise

    def download_file(self, object_name: str) -> str:
        """
        Скачивает файл из S3/MinIO во временный файл и возвращает путь к нему.
        Вызывающая сторона обязана удалить этот файл после использования!
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        try:
            self.s3_client.download_file(self.bucket_name, object_name, temp_file.name)
            logger.info("file_downloaded_from_storage", object_name=object_name, temp_path=temp_file.name)
            return temp_file.name
        except Exception as e:
            logger.error("file_download_failed", object_name=object_name, error=str(e))
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
            raise

    def delete_file(self, object_name: str) -> bool:
        """
        Удаляет файл из хранилища.
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )
            logger.info("file_deleted_from_storage", object_name=object_name)
            return True
        except Exception as e:
            logger.error("file_deletion_failed", object_name=object_name, error=str(e))
            return False


storage_service = StorageService()