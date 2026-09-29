import {
  Configuration,
  ResponseError,
  RuleHitsApi,
} from '@lingmind/annex';

const detectionsPopulate =
  'populate[evidences][populate][observation][populate][0]';

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

async function main(): Promise<void> {
  const api = new RuleHitsApi(new Configuration({
    basePath: required('LM_BASE_URL'),
    accessToken: required('LM_ACCESS_TOKEN'),
  })).withPreMiddleware(async ({ url, init }) => {
    const requestUrl = new URL(url);
    requestUrl.searchParams.set(detectionsPopulate, 'detections');
    return { url: requestUrl.toString(), init };
  });

  const response = await api.getRuleHit({
    ruleHitId: required('LM_RULE_HIT_ID'),
    xRequestedProject: required('LM_PROJECT_ID'),
  });

  for (const evidence of response.data.evidences ?? []) {
    const observation = evidence.observation;
    if (!observation) continue;

    console.log({
      evidenceCode: evidence.code,
      observationDocumentId: observation.documentId,
      detections: observation.detections ?? [],
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
