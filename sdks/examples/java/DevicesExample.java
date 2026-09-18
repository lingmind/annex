import com.lingmind.annex.ApiClient;
import com.lingmind.annex.ApiException;
import com.lingmind.annex.api.DevicesApi;
import com.lingmind.annex.model.DeviceListResponse;

public final class DevicesExample {
  private DevicesExample() {}

  private static String required(String name) {
    String value = System.getenv(name);
    if (value == null || value.isBlank()) {
      throw new IllegalStateException(name + " is required");
    }
    return value;
  }

  public static void main(String[] args) {
    ApiClient client = new ApiClient();
    client.updateBaseUri(required("LM_BASE_URL"));
    client.setRequestInterceptor(builder -> builder.header(
        "Authorization", "Bearer " + required("LM_ACCESS_TOKEN")));

    DevicesApi api = new DevicesApi(client);
    try {
      DeviceListResponse response = api.listDevices(
          required("LM_PROJECT_ID"),
          "project",
          1,
          20,
          null,
          null,
          null,
          null);

      response.getData().forEach(device -> System.out.printf(
          "%s\t%s\t%s%n",
          device.getDocumentId(),
          device.getName(),
          device.getProject() == null ? null : device.getProject().getDocumentId()));
    } catch (ApiException error) {
      System.err.printf("HTTP %d: %s%n", error.getCode(), error.getResponseBody());
      System.exit(1);
    }
  }
}
