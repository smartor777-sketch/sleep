"""Сервис для работы с файловым хранилищем (S3/MinIO)"""

import logging
import uuid
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

from config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Сервис для работы с S3/MinIO"""
    
    def __init__(self):
        """Инициализация S3 клиента"""
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name=settings.s3_region,
            config=Config(signature_version='s3v4'),
            use_ssl=settings.s3_use_ssl
        )
        self.bucket_name = settings.s3_bucket
        
        # Создаём bucket если не существует
        self._create_bucket_if_not_exists()
    
    def _create_bucket_if_not_exists(self):
        """Создать bucket если не существует"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket не существует, создаём
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Bucket {self.bucket_name} created")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
            else:
                logger.error(f"Error checking bucket: {e}")
    
    def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Загрузить файл в S3
        
        Args:
            file_content: Содержимое файла
            file_name: Имя файла
            content_type: MIME тип файла
        
        Returns:
            URL файла
        
        Raises:
            Exception: При ошибке загрузки
        """
        # Генерируем уникальное имя файла
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'jpg'
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        
        try:
            # Загружаем файл
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_name,
                Body=BytesIO(file_content),
                ContentType=content_type,
                ACL='public-read'  # Делаем файл публично доступным
            )
            
            # Формируем URL
            file_url = f"{settings.s3_endpoint}/{self.bucket_name}/{unique_name}"
            logger.info(f"File uploaded: {file_url}")
            
            return file_url
        
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise Exception(f"Failed to upload file: {e}")
    
    def delete_file(self, file_url: str):
        """
        Удалить файл из S3
        
        Args:
            file_url: URL файла
        """
        try:
            # Извлекаем имя файла из URL
            file_key = file_url.split('/')[-1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            logger.info(f"File deleted: {file_url}")
        
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
    
    def get_file_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Получить подписанный URL для файла
        
        Args:
            file_key: Ключ файла в S3
            expires_in: Время жизни URL в секундах
        
        Returns:
            Подписанный URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise


# Глобальный экземпляр сервиса
storage_service = StorageService()

