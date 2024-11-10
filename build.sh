PROJECT_ID=gcp-transcribe-test
REPOSITORY=insane-whisper
BUILD=transcribe

gcloud builds submit \
  --tag us-central1-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/test \
