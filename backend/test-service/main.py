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
            # Try to register test user
            test_user = {
                "email": "test2@example.com",
                "password": "testpassword",
                "name": "Test User"
            }
            
            response = await self.client.post(
                f"{self.auth_service}/auth/register",
                json=test_user
            )
            
            if response.status_code == 200:
                logger.info("Successfully registered new test user")
                self.log_result("Auth Service - Registration", True)
            elif response.status_code == 400 and "already registered" in response.text:
                logger.info("Test user already exists, proceeding with login")
                self.log_result("Auth Service - Registration (User Exists)", True)
            else:
                logger.error(f"Registration failed unexpectedly: {response.text}")
                raise Exception(f"Registration failed unexpectedly: {response.text}")

            # Login and get token
            login_data = {
                "username": test_user["email"],
                "password": test_user["password"],
                "grant_type": "password",
                "scope": ""
            }
            
            logger.info(f"Attempting to login with email: {test_user['email']}")
            response = await self.client.post(
                f"{self.auth_service}/auth/token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Login failed: {response.text}")
                raise Exception(f"Login failed: {response.text}")
                
            token_data = response.json()
            self.auth_token = token_data.get("access_token")
            
            if not self.auth_token:
                logger.error("No token received from login")
                raise Exception("No token received from login")
                
            logger.info("Successfully obtained auth token")
            self.log_result("Auth Service - Login", True)

        except Exception as e:
            logger.error(f"Auth service test failed: {str(e)}")
            self.log_result("Auth Service", False, str(e))
            raise

    async def test_api_gateway(self):
        try:
            if not self.auth_token:
                raise Exception("No auth token available")
            
            logger.info(f"Using auth token: {self.auth_token[:10]}...")  # Log first 10 chars
            
            # Test getting workspaces
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            logger.info(f"Making request with headers: {headers}")
            
            response = await self.client.get(
                f"{self.api_gateway}/api/v1/workspaces",
                headers=headers
            )
            
            logger.info(f"Get workspaces response status: {response.status_code}")
            logger.info(f"Get workspaces response body: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"Get workspaces failed: {response.text}")
                raise Exception(f"Get workspaces failed: {response.text}")
                
            workspaces = response.json().get("workspaces", [])
            if not workspaces:
                logger.warning("No workspaces found for user")
            else:
                logger.info(f"Found {len(workspaces)} workspaces")
                
            self.log_result("API Gateway - Get Workspaces", True)

            # Upload recording
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