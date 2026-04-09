import asyncio
import logging
from datetime import datetime

from .event import Reminder

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self):
        self.scheduled_reminders: dict[str, asyncio.Task] = {}
        self.reminder_callbacks: dict[str, callable] = {}

    async def schedule_reminder(self, reminder: Reminder) -> bool:
        try:
            if reminder.reminder_id in self.scheduled_reminders:
                logger.warning(
                    f"Reminder {reminder.reminder_id} already scheduled, cancelling old one"
                )
                await self.cancel_reminder(reminder.reminder_id)

            now = datetime.now()
            if reminder.remind_at <= now:
                logger.warning(
                    f"Reminder {reminder.reminder_id} time is in the past, skipping"
                )
                return False

            delay = (reminder.remind_at - now).total_seconds()

            async def reminder_task():
                await asyncio.sleep(delay)
                await self.send_notification(reminder)

            task = asyncio.create_task(reminder_task())
            self.scheduled_reminders[reminder.reminder_id] = task

            logger.info(
                f"Scheduled reminder {reminder.reminder_id} for {reminder.remind_at}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to schedule reminder {reminder.reminder_id}: {e}")
            return False

    async def cancel_reminder(self, reminder_id: str) -> bool:
        try:
            if reminder_id not in self.scheduled_reminders:
                logger.warning(f"Reminder {reminder_id} not found in scheduled reminders")
                return False

            task = self.scheduled_reminders[reminder_id]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del self.scheduled_reminders[reminder_id]
            logger.info(f"Cancelled reminder {reminder_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel reminder {reminder_id}: {e}")
            return False

    async def process_due_reminders(self) -> list[Reminder]:
        due_reminders: list[Reminder] = []

        for reminder_id, task in list(self.scheduled_reminders.items()):
            if task.done():
                try:
                    task.result()
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Reminder task {reminder_id} failed: {e}")

        return due_reminders

    async def send_notification(self, reminder: Reminder) -> bool:
        try:
            logger.info(
                f"Sending {reminder.method} notification for reminder {reminder.reminder_id}"
            )

            if reminder.method == "email":
                await self._send_email_notification(reminder)
            elif reminder.method == "push":
                await self._send_push_notification(reminder)
            elif reminder.method == "sms":
                await self._send_sms_notification(reminder)

            reminder.sent = True
            logger.info(f"Successfully sent notification for reminder {reminder.reminder_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to send notification for reminder {reminder.reminder_id}: {e}"
            )
            return False

    async def _send_email_notification(self, reminder: Reminder):
        logger.info(f"Sending email notification for event {reminder.event_id}")
        await asyncio.sleep(0.1)

    async def _send_push_notification(self, reminder: Reminder):
        logger.info(f"Sending push notification for event {reminder.event_id}")
        await asyncio.sleep(0.1)

    async def _send_sms_notification(self, reminder: Reminder):
        logger.info(f"Sending SMS notification for event {reminder.event_id}")
        await asyncio.sleep(0.1)

    def register_callback(self, reminder_id: str, callback: callable):
        self.reminder_callbacks[reminder_id] = callback

    def unregister_callback(self, reminder_id: str):
        if reminder_id in self.reminder_callbacks:
            del self.reminder_callbacks[reminder_id]

    def get_scheduled_count(self) -> int:
        return len(self.scheduled_reminders)

    def clear_all(self):
        for task in self.scheduled_reminders.values():
            task.cancel()
        self.scheduled_reminders.clear()
        logger.info("Cleared all scheduled reminders")
