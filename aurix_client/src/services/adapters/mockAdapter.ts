export class MockAdapter {
  public static async simulateDelay(ms = 350): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}