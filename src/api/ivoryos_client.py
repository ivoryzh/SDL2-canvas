from typing import Optional

import httpx


class IvoryOSClient:

    def __init__(self, client_url: str = None, username: str = None, password: str = None):
        self.url = client_url or "http://127.0.0.1:8000/ivoryos"
        self.username = username
        self.password = password
        self.login_data = {
            "username": self.username or "admin",
            "password": self.password or "admin",
        }
        self.ivoryos_client = httpx.Client(follow_redirects=True, timeout=None)

    def _check_authentication(self):
        try:
            resp = self.ivoryos_client.get(f"{self.url}/", follow_redirects=False)
            if resp.status_code == httpx.codes.OK:
                return
            login_resp = self.ivoryos_client.post(f"{self.url}/auth/login", data=self.login_data)
            if login_resp.status_code != 200:
                raise RuntimeError(f"Login failed")
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection error during authentication: {e}") from e

    def submit_workflow_script(self, workflow_name: str, main_script: str = "", cleanup_script: str = "",
                               prep_script: str = "") -> str:
        """get current workflow script"""
        try:
            self._check_authentication()
            resp = self.ivoryos_client.post(url=f"{self.url}/api/design/submit",
                                       json={
                                           "workflow_name": workflow_name,
                                           "script": main_script,
                                           "cleanup": cleanup_script,
                                           "prep": prep_script
                                       })
            if resp.status_code == httpx.codes.OK:
                return "Updated"
            else:
                return f"Error submitting workflow script: {resp.status_code}"
        except Exception as e:
            return f"Error submitting workflow script: {str(e)}"

    def run_workflow(self, repeat_time: Optional[int] = None) -> str:
        """
        run the loaded workflow with repeat times
        :param repeat_time:
        :return:
        """
        try:
            self._check_authentication()
            resp = self.ivoryos_client.post(f"{self.url}/design/campaign", json={"repeat": str(repeat_time)})
            if resp.status_code == httpx.codes.OK:
                return resp.json()
            else:
                return f"Error starting workflow execution: {resp.status_code}"
        except Exception as e:
            return f"Error starting workflow execution: {str(e)}"

    def execute_task(self, component: str, method: str, kwargs: dict) -> str:
        """
        Execute a robot task and return task_id.
        :param component: deck component (e.g. sdl)
        :param method: method name (e.g. dose_solid)
        :param kwargs: method keyword arguments (e.g. {'amount_in_mg': '5'})
        :return: {'status': 'task started', 'task_id': 7}
        """
        try:
            self._check_authentication()
            if kwargs is None:
                kwargs = {}
            snapshot = self.ivoryos_client.get(f"{self.url}/api/control").json()
            component = component if component.startswith("deck.") else f"deck.{component}"
            if component not in snapshot:
                return f"The component {component} does not exist in {snapshot}."
            kwargs["hidden_name"] = method
            # only submit the task without waiting for completion.
            kwargs["hidden_wait"] = True
            resp = self.ivoryos_client.post(f"{self.url}/api/control/{component}", data=kwargs)
            if resp.status_code == httpx.codes.OK:
                result = resp.json()
                return result
            else:
                return f"Error submitting tasks {resp.status_code}"
        except Exception as e:
            return f"Error submitting tasks {str(e)}"
