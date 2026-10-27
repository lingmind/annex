import {
  Configuration,
  ResponseError,
  RuleHitsApi,
} from '@lingmind/annex';

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
    requestUrl.searchParams.set('populate[evidences][populate][0]', 'device');
    requestUrl.searchParams.set('populate[evidences][populate][1]', 'rawDatum');
    return { url: requestUrl.toString(), init };
  });

  const response = await api.getRuleHit({
    ruleHitId: required('LM_RULE_HIT_ID'),
    xRequestedProject: required('LM_PROJECT_ID'),
  });

  for (const evidence of response.data.evidences ?? []) {
    console.log({
      evidenceCode: evidence.code,
      sourceKind: evidence.sourceKind,
      sourceId: evidence.sourceId,
      occurredAt: evidence.occurredAt,
      mediaRef: evidence.mediaRef,
      overlaySvg: evidence.overlaySvg,
      summary: evidence.summary,
      device: evidence.device,
      rawDatum: evidence.rawDatum,
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
