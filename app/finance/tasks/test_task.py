from celery import shared_task


@shared_task
def test_celery_task() -> str:
    return "Celery is working!"
