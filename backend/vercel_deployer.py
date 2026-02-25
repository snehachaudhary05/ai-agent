"""
Vercel Deployment Manager
Handles automated deployment of React websites to Vercel
"""

import os
import re
import json
import httpx
import tarfile
import io
import base64
from typing import Dict, Optional, List
from pathlib import Path
import asyncio

class VercelDeployer:
    """Manages Vercel deployments for generated React websites"""

    def __init__(self):
        self.token = os.getenv("VERCEL_TOKEN")
        self.team_id = os.getenv("VERCEL_TEAM_ID")  # Optional
        # Force deploy to personal account for public access (ignore team settings)
        self.team_id = None  # Always use personal account
        self.base_url = "https://api.vercel.com"

        if not self.token:
            print("[WARNING]  Warning: VERCEL_TOKEN not configured")
            self.enabled = False
        else:
            self.enabled = True
            print("[OK] Vercel deployer initialized (personal account mode)")

    def is_enabled(self) -> bool:
        """Check if Vercel is properly configured"""
        return self.enabled

    async def create_deployment(
        self,
        project_name: str,
        files: Dict[str, str],
        env_vars: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """
        Deploy a React website to Vercel

        Args:
            project_name: Name for the Vercel project (will be slugified)
            files: Dictionary of {file_path: file_content}
                   Example: {"package.json": "...", "src/App.jsx": "..."}
            env_vars: Optional environment variables

        Returns:
            Dict with deployment info including URL
            {
                "url": "https://project-abc123.vercel.app",
                "id": "dpl_...",
                "status": "ready",
                "project_id": "prj_..."
            }
        """
        if not self.enabled:
            return None

        try:
            # Prepare files for deployment
            deployment_files = []
            for file_path, content in files.items():
                deployment_files.append({
                    "file": file_path,
                    "data": content
                })

            # Prepare deployment payload
            payload = {
                "name": self._slugify(project_name),
                "files": deployment_files,
                "projectSettings": {
                    "framework": "vite",
                    "buildCommand": "npm run build",
                    "outputDirectory": "dist",
                    "installCommand": "npm install",
                    "devCommand": "npm run dev"
                },
                "target": "production"
                # Note: gitSource omitted - not needed for file-based deployments
            }

            # Add environment variables if provided
            if env_vars:
                payload["env"] = env_vars

            # Don't add team ID - deploy to personal account for public access
            # if self.team_id:
            #     payload["teamId"] = self.team_id

            # Make deployment request
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/v13/deployments",
                    headers=headers,
                    json=payload
                )

                if response.status_code in [200, 201]:
                    data = response.json()

                    deployment_id = data.get('id')
                    project_id = data.get('projectId')

                    # Wait for deployment to be ready
                    await self._wait_for_deployment(deployment_id)

                    # Disable all protection on the project
                    if project_id:
                        await self.update_project_protection(project_id)

                    # Re-fetch deployment details AFTER it is ready — the
                    # initial POST response does not yet have the production alias.
                    deployment_url = f"https://{data.get('url')}"  # fallback
                    alias_list = []
                    async with httpx.AsyncClient(timeout=30.0) as fetch_client:
                        detail_resp = await fetch_client.get(
                            f"{self.base_url}/v13/deployments/{deployment_id}",
                            headers=headers
                        )
                        if detail_resp.status_code == 200:
                            details = detail_resp.json()
                            alias_list = details.get('alias', [])

                    if alias_list:
                        # Pick the production alias — it has NO random hex hash suffix.
                        # Hash URLs look like: name-abc1def2.vercel.app
                        # Production URLs look like: name.vercel.app or name-username.vercel.app
                        def _is_production(alias: str) -> bool:
                            subdomain = alias.replace('.vercel.app', '')
                            return not re.search(r'-[0-9a-f]{8,}$', subdomain)

                        production = [a for a in alias_list if _is_production(a)]
                        chosen = production[0] if production else alias_list[0]
                        deployment_url = f"https://{chosen}"

                    print(f"[OK] Deployed successfully: {deployment_url}")
                    return {
                        "url": deployment_url,
                        "id": deployment_id,
                        "status": "ready",
                        "alias": alias_list,
                        "project_id": project_id
                    }
                else:
                    error_msg = response.json() if response.text else response.text
                    print(f"[ERROR] Vercel deployment failed: {error_msg}")
                    return None

        except Exception as e:
            print(f"[ERROR] Error deploying to Vercel: {e}")
            return None

    async def _wait_for_deployment(self, deployment_id: str, max_attempts: int = 45) -> bool:
        """Wait for deployment to be ready (poll status)"""
        if not self.enabled:
            return False

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/v13/deployments/{deployment_id}",
                        headers=headers
                    )

                    if response.status_code == 200:
                        data = response.json()
                        state = data.get('readyState', 'INITIALIZING')

                        if state == 'READY':
                            print(f"[OK] Deployment {deployment_id} is ready!")
                            return True
                        elif state == 'ERROR':
                            print(f"[ERROR] Deployment {deployment_id} failed")
                            return False

                        # Still building, wait and retry
                        await asyncio.sleep(2)
                    else:
                        print(f"[WARNING] Poll attempt {attempt+1}: status {response.status_code}")
                        await asyncio.sleep(2)

            except Exception as e:
                print(f"[WARNING] Error checking deployment status: {e}")
                await asyncio.sleep(2)

        print(f"[WARNING] Deployment {deployment_id} timed out after {max_attempts * 2}s")
        return False

    async def get_deployment(self, deployment_id: str) -> Optional[Dict]:
        """Get deployment details"""
        if not self.enabled:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v13/deployments/{deployment_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return None

        except Exception as e:
            print(f"[ERROR] Error getting deployment: {e}")
            return None

    async def list_deployments(self, project_id: Optional[str] = None) -> List[Dict]:
        """List all deployments (optionally filtered by project)"""
        if not self.enabled:
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            params = {}
            if project_id:
                params["projectId"] = project_id
            if self.team_id:
                params["teamId"] = self.team_id

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v6/deployments",
                    headers=headers,
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("deployments", [])
                else:
                    return []

        except Exception as e:
            print(f"[ERROR] Error listing deployments: {e}")
            return []

    async def delete_deployment(self, deployment_id: str) -> bool:
        """Delete a deployment"""
        if not self.enabled:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/v13/deployments/{deployment_id}",
                    headers=headers
                )

                return response.status_code == 200

        except Exception as e:
            print(f"[ERROR] Error deleting deployment: {e}")
            return False

    async def create_project(self, project_name: str, framework: str = "vite") -> Optional[Dict]:
        """Create a new Vercel project"""
        if not self.enabled:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            payload = {
                "name": self._slugify(project_name),
                "framework": framework
            }

            if self.team_id:
                payload["teamId"] = self.team_id

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v9/projects",
                    headers=headers,
                    json=payload
                )

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    return None

        except Exception as e:
            print(f"[ERROR] Error creating project: {e}")
            return None

    async def update_project_protection(self, project_id: str) -> bool:
        """Update project to disable password protection for public access"""
        if not self.enabled:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            # Disable password protection to allow public access
            payload = {
                "passwordProtection": None,  # Disable password protection
                "ssoProtection": None  # Disable SSO protection if applicable
            }

            url = f"{self.base_url}/v9/projects/{project_id}"
            if self.team_id:
                url += f"?teamId={self.team_id}"

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    url,
                    headers=headers,
                    json=payload
                )

                if response.status_code in [200, 201]:
                    print(f"[OK] Project {project_id} set to public access")
                    return True
                else:
                    print(f"[WARNING] Could not update project protection: {response.text}")
                    return False

        except Exception as e:
            print(f"[ERROR] Error updating project protection: {e}")
            return False

    async def deploy_static_html(self, project_name: str, html_content: str) -> Optional[Dict]:
        """
        Deploy a single self-contained HTML file as a static Vercel site.
        This makes the deployed site look identical to the in-app preview.
        """
        if not self.enabled:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            payload = {
                "name": self._slugify(project_name),
                "files": [
                    {"file": "index.html", "data": html_content}
                ],
                "projectSettings": {
                    "framework": None,        # Static — no build step needed
                    "buildCommand": None,
                    "outputDirectory": None,
                    "installCommand": None
                },
                "target": "production"
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/v13/deployments",
                    headers=headers,
                    json=payload
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    deployment_id = data.get('id')
                    project_id = data.get('projectId')

                    ready = await self._wait_for_deployment(deployment_id)
                    if not ready:
                        print(f"[ERROR] Deployment {deployment_id} did not reach READY state — aborting")
                        return None
                    if project_id:
                        await self.update_project_protection(project_id)

                    deployment_url = f"https://{data.get('url')}"
                    alias_list = []
                    async with httpx.AsyncClient(timeout=30.0) as fc:
                        dr = await fc.get(
                            f"{self.base_url}/v13/deployments/{deployment_id}",
                            headers=headers
                        )
                        if dr.status_code == 200:
                            alias_list = dr.json().get('alias', [])

                    if alias_list:
                        def _is_prod(a):
                            return not re.search(r'-[0-9a-f]{8,}$', a.replace('.vercel.app', ''))
                        prod = [a for a in alias_list if _is_prod(a)]
                        deployment_url = f"https://{prod[0] if prod else alias_list[0]}"

                    print(f"[OK] Static HTML deployed: {deployment_url}")
                    return {"url": deployment_url, "id": deployment_id, "status": "ready"}
                else:
                    print(f"[ERROR] Static deploy failed: {response.json()}")
                    return None

        except Exception as e:
            print(f"[ERROR] deploy_static_html error: {e}")
            return None

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug"""
        import re
        # Convert to lowercase
        text = text.lower()
        # Replace spaces and special chars with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)
        # Remove leading/trailing hyphens
        text = text.strip('-')
        # Limit length
        return text[:50]

    def generate_vercel_config(self, framework: str = "vite") -> Dict:
        """Generate vercel.json configuration"""
        if framework == "vite":
            return {
                "buildCommand": "npm run build",
                "outputDirectory": "dist",
                "devCommand": "npm run dev",
                "installCommand": "npm install",
                "framework": "vite"
            }
        elif framework == "nextjs":
            return {
                "buildCommand": "npm run build",
                "outputDirectory": ".next",
                "devCommand": "npm run dev",
                "installCommand": "npm install",
                "framework": "nextjs"
            }
        else:
            return {}


# Global Vercel deployer instance
vercel_deployer = VercelDeployer()
