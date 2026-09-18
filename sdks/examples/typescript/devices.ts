import {
  Configuration,
  DevicesApi,
  ResponseError,
} from '@lingmind/annex';

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

async function main(): Promise<void> {
  const api = new DevicesApi(new Configuration({
    basePath: required('LM_BASE_URL'),
    accessToken: required('LM_ACCESS_TOKEN'),
  }));

  const response = await api.listDevices({
    xRequestedProject: required('LM_PROJECT_ID'),
    populate: 'project',
    paginationPage: 1,
    paginationPageSize: 20,
  });

  for (const device of response.data) {
    console.log({
      documentId: device.documentId,
      name: device.name,
      projectDocumentId: device.project?.documentId,
    });
  }
}

main().catch(async (error: unknown) => {
  if (error instanceof ResponseError) {
    console.error(`HTTP ${error.response.status}: ${await error.response.text()}`);
  } else {
    console.error(error);
  }
  process.exitCode = 1;
});
