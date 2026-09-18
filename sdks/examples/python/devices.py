import asyncio
import os

import lingmind_annex
from lingmind_annex.api.devices_api import DevicesApi
from lingmind_annex.exceptions import ApiException


def required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


async def main() -> None:
    configuration = lingmind_annex.Configuration(
        host=required("LM_BASE_URL"),
        access_token=required("LM_ACCESS_TOKEN"),
    )

    async with lingmind_annex.ApiClient(configuration) as client:
        response = await DevicesApi(client).list_devices(
            x_requested_project=required("LM_PROJECT_ID"),
            populate="project",
            pagination_page=1,
            pagination_page_size=20,
        )

    for device in response.data:
        print(
            {
                "documentId": device.document_id,
                "name": device.name,
                "projectDocumentId": (
                    device.project.document_id if device.project else None
                ),
            }
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ApiException as error:
        print(f"HTTP {error.status}: {error.body}")
        raise SystemExit(1) from error
