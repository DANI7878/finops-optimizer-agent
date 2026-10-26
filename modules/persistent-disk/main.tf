resource "google_compute_disk" "this" {
  name   = var.name
  zone   = var.zone
  type   = var.type
  size   = var.size_gb
  labels = var.labels
}

resource "google_compute_snapshot" "this" {
  count = var.create_snapshot ? 1 : 0

  name        = coalesce(var.snapshot_name, "${var.name}-snap")
  zone        = var.zone
  source_disk = google_compute_disk.this.name
  labels      = var.labels
}
