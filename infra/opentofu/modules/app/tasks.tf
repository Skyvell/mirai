# Async lab-PDF parsing: the API enqueues here, Cloud Tasks calls the worker
# endpoint back with an OIDC token. max_concurrent_dispatches caps in-flight
# LLM parses (cost control); retries cover transient failures.
resource "google_cloud_tasks_queue" "parse" {
  name     = "mirai-lab-parse"
  location = var.tasks_location

  rate_limits {
    max_concurrent_dispatches = 5
    max_dispatches_per_second = 5
  }

  retry_config {
    max_attempts       = 5
    min_backoff        = "10s"
    max_backoff        = "300s"
    max_retry_duration = "3600s"
  }

  depends_on = [google_project_service.required]
}
