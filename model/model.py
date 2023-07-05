import io
import os
import base64
import concurrent.futures
from aiohttp import ClientSession, ClientTimeout
from PIL import Image

__all__ = ["Model"]

headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_API_TOKEN')}"}
TIMEOUT = 28

class ModelException(Exception):
    pass

class Model:
    def __init__(self, selected_model, prompt, negative_prompt):
        self.selected_model = selected_model
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.params = {
            "inputs": self.prompt,
            "parameters": {
                "negative_prompt": self.negative_prompt,
                "guidance_scale": 7.5,
                "num_inference_steps": 25,
                "height": 512,
                "width": 512,
            },
            "options": {
                "seed": 42,
                "temperature": 0.5,
                "use_cache": False,
                "wait_for_model": True
            }
        }
        self.retry_count = 0

    async def generate_image(self):
        try:
            base_64_image = await self._generate_image()
            return base_64_image
        except concurrent.futures.TimeoutError:
            return "timeout"

    async def _generate_image(self):
        try:
            response_content = await self.fetch_response()
            if not response_content:
                raise ModelException("No content in the response")
        
            image = Image.open(io.BytesIO(response_content))
            image_byte_data = io.BytesIO()
            image.save(image_byte_data, format='PNG')
            base_64_image = base64.b64encode(image_byte_data.getvalue()).decode('utf-8')
            return base_64_image
        except Exception as e:
            print(f"Failed to generate image: {e}")
            raise ModelException(f"Failed to generate image: {e}") from e

    async def fetch_response(self):
        timeout = ClientTimeout(total=TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            try:
                response = await session.post(
                    self.selected_model,
                    headers=headers,
                    json=self.params,
                )
            except Exception as e:
                print(f"RequestException: {e}")
                raise ModelException(f"RequestException: {e}") from e

            if response.status != 200:
                print(f"Failed to generate image: {response.status}")
                print(f"Response text: {response.text}")
                if response.status == 400:
                    raise ModelException("Bad Request - there might be something wrong with your parameters.")
                elif response.status == 401:
                    raise ModelException("Unauthorized - there might be something wrong with your authentication.")
                else:
                    raise ModelException(f"Unexpected status code: {response.status}")

            return await response.read()