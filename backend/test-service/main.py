import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestService:
    def __init__(self):
        self.api_gateway = "http://api-gateway:8000"
        self.auth_service = "http://auth-service:8000"
        self.recording_service = "http://recording-service:8000"
        self.transcription_service = "http://transcription-service:8000"
        self.summarization_service = "http://summarization-service:8000"
        self.test_results = []
        self.auth_token = None
        self.client = None
        self.recording_id = None  # Initialize recording_id

    async def setup(self):
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(timeout=30.0)  # Increased timeout
        
    async def cleanup(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    async def run_all_tests(self):
        try:
            logger.info("Starting test suite...")
            await self.setup()
            
            # Auth Service Tests
            await self.test_auth_service()
            
            # API Gateway Tests
            await self.test_api_gateway()
            
            # Integration Tests
            if self.recording_id:
                await self.test_transcription_service()
                await self.test_summarization_service()
                await self.test_full_pipeline()
            
            self.print_results()
        finally:
            await self.cleanup()

    async def test_auth_service(self):
        try:
            # Test registration with all required fields
            register_data = {
                "email": f"test_{datetime.now().timestamp()}@test.com",
                "password": "test123",
                "name": "Test User"
            }
            
            # Send as JSON body
            response = await self.client.post(
                f"{self.auth_service}/auth/register",
                json=register_data  # Changed from params to json
            )
            
            if response.status_code != 200:
                logger.error(f"Registration failed: {response.text}")
                raise Exception(f"Registration failed: {response.text}")
                
            self.log_result("Auth Service - Registration", True)

            # Test login with correct credentials
            login_data = {
                "username": register_data["email"],
                "password": register_data["password"]
            }
            
            # Send as form data for login
            login_response = await self.client.post(
                f"{self.auth_service}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if login_response.status_code != 200:
                logger.error(f"Login failed: {login_response.text}")
                raise Exception(f"Login failed: {login_response.text}")
                
            self.auth_token = login_response.json()["access_token"]
            self.log_result("Auth Service - Login", True)

        except Exception as e:
            logger.error(f"Auth Service test failed: {str(e)}")
            self.log_result("Auth Service", False, str(e))
            raise  # Re-raise to stop further tests

    async def test_api_gateway(self):
        try:
            if not self.auth_token:
                raise Exception("No auth token available")

            # Create test audio file
            test_audio_path = "test_audio.m4a"
            with open(test_audio_path, "wb") as f:
                f.write(b"test audio content")

            # Create test project first
            project_response = await self.client.post(
                f"{self.api_gateway}/api/v1/projects",
                json={
                    "name": "Test Project",
                    "description": "Test Project Description",
                    "owner_id": "507f1f77bcf86cd799439011"  # Test user ID
                },
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if project_response.status_code != 200:
                logger.error(f"Project creation failed: {project_response.text}")
                raise Exception(f"Project creation failed: {project_response.text}")
                
            project_id = project_response.json()["project_id"]

            # Create test workspace
            workspace_response = await self.client.post(
                f"{self.api_gateway}/api/v1/projects/{project_id}/workspaces",
                json={
                    "name": "Test Workspace",
                    "description": "Test Workspace Description"
                },
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            if workspace_response.status_code != 200:
                logger.error(f"Workspace creation failed: {workspace_response.text}")
                raise Exception(f"Workspace creation failed: {workspace_response.text}")
                
            workspace_id = workspace_response.json()["workspace_id"]

            # Upload recording
            with open(test_audio_path, "rb") as f:
                files = {
                    "file": ("test_audio.m4a", f, "audio/m4a")
                }
                data = {
                    "workspace_id": workspace_id,
                    "user_id": "507f1f77bcf86cd799439011",  # Added user_id
                    "title": "Test Recording",
                    "description": "Test recording description"
                }
                
                response = await self.client.post(
                    f"{self.api_gateway}/api/v1/meetings/record",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
            
            if response.status_code != 200:
                logger.error(f"Recording upload failed: {response.text}")
                raise Exception(f"Recording upload failed: {response.text}")
                
            self.recording_id = response.json()["recording_id"]
            self.log_result("API Gateway - Recording Upload", True)

            os.remove(test_audio_path)
        except Exception as e:
            logger.error(f"API Gateway test failed: {str(e)}")
            self.log_result("API Gateway", False, str(e))
            raise  # Re-raise to stop further tests

    async def test_transcription_service(self):
        try:
            if not self.recording_id:
                raise Exception("No recording ID available")

            response = await self.client.post(
                f"{self.api_gateway}/api/v1/meetings/transcribe/{self.recording_id}",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            assert response.status_code == 200
            self.log_result("Transcription Service", True)
        except Exception as e:
            logger.error(f"Transcription Service test failed: {str(e)}")
            self.log_result("Transcription Service", False, str(e))

    async def test_summarization_service(self):
        try:
            if not self.recording_id:
                raise Exception("No recording ID available")

            # Wait for transcription to complete
            await asyncio.sleep(5)

            response = await self.client.get(
                f"{self.api_gateway}/api/v1/meetings/{self.recording_id}/summary",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            assert response.status_code == 200
            self.log_result("Summarization Service", True)
        except Exception as e:
            logger.error(f"Summarization Service test failed: {str(e)}")
            self.log_result("Summarization Service", False, str(e))

    async def test_full_pipeline(self):
        try:
            # Test the complete flow through the API Gateway
            test_audio_path = "test_audio.m4a"
            with open(test_audio_path, "wb") as f:
                f.write(b"test audio content")

            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Create project first
                project_response = await client.post(
                    f"{self.api_gateway}/api/v1/projects",
                    json={
                        "name": "Test Pipeline Project",
                        "description": "Test Pipeline Project Description",
                        "owner_id": "507f1f77bcf86cd799439011"
                    },
                    headers=headers
                )
                project_id = project_response.json()["project_id"]

                # Create workspace
                workspace_response = await client.post(
                    f"{self.api_gateway}/api/v1/projects/{project_id}/workspaces",
                    json={
                        "name": "Test Pipeline Workspace",
                        "description": "Test Pipeline Workspace Description"
                    },
                    headers=headers
                )
                workspace_id = workspace_response.json()["workspace_id"]

                # Upload recording
                with open(test_audio_path, "rb") as f:
                    files = {"file": ("test_audio.m4a", f, "audio/m4a")}
                    data = {
                        "workspace_id": workspace_id,
                        "user_id": "507f1f77bcf86cd799439011",
                        "title": "Test Pipeline Recording",
                        "description": "Test pipeline recording description"
                    }
                    response = await client.post(
                        f"{self.api_gateway}/api/v1/meetings/record",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    assert response.status_code == 200
                    meeting_id = response.json()["recording_id"]

                # Wait for processing
                await asyncio.sleep(5)

                # Get summary
                response = await client.get(
                    f"{self.api_gateway}/api/v1/meetings/{meeting_id}/summary",
                    headers=headers
                )
                assert response.status_code == 200
                
                self.log_result("Full Pipeline Integration", True)

            os.remove(test_audio_path)

        except Exception as e:
            self.log_result("Full Pipeline Integration", False, str(e))

    def log_result(self, test_name: str, success: bool, error: str = None):
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "error": error if error else None
        }
        self.test_results.append(result)
        
        # Print result immediately
        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}")
        if error:
            logger.error(f"   Error: {error}")

    def print_results(self):
        logger.info("\nTest Results Summary:")
        logger.info("=" * 50)
        success_count = sum(1 for r in self.test_results if r["success"])
        total_count = len(self.test_results)
        logger.info(f"Passed: {success_count}/{total_count}")
        logger.info("=" * 50)

async def main():
    test_service = TestService()
    await test_service.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 