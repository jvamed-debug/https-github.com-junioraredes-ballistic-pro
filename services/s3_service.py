import boto3
import streamlit as st
from botocore.exceptions import NoCredentialsError
import os

class S3Service:
    def __init__(self):
        try:
            self.s3_config = st.secrets.get("aws_s3", {})
            self.bucket_name = self.s3_config.get("bucket_name")
            self.region = self.s3_config.get("region_name", "us-east-1")
            
            if self.bucket_name:
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=self.s3_config.get("aws_access_key_id"),
                    aws_secret_access_key=self.s3_config.get("aws_secret_access_key"),
                    region_name=self.region
                )
            else:
                self.client = None
        except Exception:
            self.client = None

    def upload_image(self, file, folder="targets"):
        """Realiza o upload de uma imagem para o bucket S3."""
        if not self.client:
            return None
        
        try:
            filename = f"{folder}/{os.urandom(8).hex()}_{file.name}"
            self.client.upload_fileobj(
                file,
                self.bucket_name,
                filename,
                ExtraArgs={'ContentType': file.type}
            )
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
        except Exception as e:
            st.error(f"Erro no upload S3: {e}")
            return None

    def delete_image(self, url):
        """Remove uma imagem do bucket dado a sua URL."""
        if not self.client or not url:
            return False
            
        try:
            key = url.split(f"{self.bucket_name}.s3.{self.region}.amazonaws.com/")[-1]
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

# Instância Singleton para uso no app
s3_mgr = S3Service()
