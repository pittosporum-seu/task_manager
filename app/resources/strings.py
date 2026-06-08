class Strings:
    _DATA = {
        "window_main_title": {
            "cn": "四象限任务管理",
            "en": "Quadrant Task Manager",
        },
        "notification_title": {
            "cn": "任务提醒",
            "en": "Task Reminder",
        },
        "notification_body": {
            "cn": "即将开始：{title}",
            "en": "Upcoming: {title}",
        },
        "menu_delete": {
            "cn": "删除任务",
            "en": "Delete Task",
        },
        "app_title": {
            "cn": "我的任务",
            "en": "My Tasks",
        },
        "btn_add_task": {
            "cn": "+ 新建任务",
            "en": "+ Add New Task",
        },
        "subtitle_inbox": {
            "cn": "收件箱",
            "en": "Inbox",
        },
        "btn_archive": {
            "cn": "归档箱",
            "en": "Archive",
        },
        "q1_title": {
            "cn": "重要且紧急",
            "en": "Important and Urgent",
        },
        "q2_title": {
            "cn": "重要不紧急",
            "en": "Important, Not Urgent",
        },
        "q3_title": {
            "cn": "紧急不重要",
            "en": "Urgent, Not Important",
        },
        "q4_title": {
            "cn": "不紧急不重要",
            "en": "Not Urgent, Not Important",
        },
        "dialog_add_title": {
            "cn": "新建任务",
            "en": "New Task",
        },
        "dialog_edit_title": {
            "cn": "编辑任务",
            "en": "Edit Task",
        },
        "label_title": {
            "cn": "标题",
            "en": "Title",
        },
        "placeholder_title": {
            "cn": "准备做什么？",
            "en": "What needs to be done?",
        },
        "label_desc": {
            "cn": "描述",
            "en": "Description",
        },
        "placeholder_desc": {
            "cn": "添加详细描述...",
            "en": "Add details...",
        },
        "label_deadline": {
            "cn": "截止时间",
            "en": "Due Date",
        },
        "label_has_date": {
            "cn": "设置截止时间",
            "en": "Set due date",
        },
        "label_has_time": {
            "cn": "包含具体时间",
            "en": "Include time",
        },
        "label_reminder": {
            "cn": "提醒",
            "en": "Reminder",
        },
        "remind_none": {
            "cn": "无提醒",
            "en": "No Reminder",
        },
        "remind_on_time": {
            "cn": "准时提醒",
            "en": "At time of event",
        },
        "remind_5min": {
            "cn": "提前 5 分钟",
            "en": "5 min before",
        },
        "remind_15min": {
            "cn": "提前 15 分钟",
            "en": "15 min before",
        },
        "remind_30min": {
            "cn": "提前 30 分钟",
            "en": "30 min before",
        },
        "remind_1h": {
            "cn": "提前 1 小时",
            "en": "1 hour before",
        },
        "remind_1d": {
            "cn": "提前 1 天",
            "en": "1 day before",
        },
        "btn_save": {
            "cn": "保存",
            "en": "Save",
        },
        "btn_cancel": {
            "cn": "取消",
            "en": "Cancel",
        },
        "archive_window_title": {
            "cn": "任务归档",
            "en": "Task Archive",
        },
        "archive_title": {
            "cn": "历史完成记录",
            "en": "Completed History",
        },
        "archive_empty": {
            "cn": "还没有完成记录",
            "en": "No completed tasks yet",
        },
        "btn_close": {
            "cn": "关闭",
            "en": "Close",
        },
        "card_due_prefix": {
            "cn": "截止",
            "en": "Due",
        },
        "card_reminder": {
            "cn": "提醒",
            "en": "Reminder",
        },
    }

    current_lang = "cn"

    @classmethod
    def get(cls, key: str, **kwargs) -> str:
        item = cls._DATA.get(key, {})
        text = item.get(cls.current_lang, item.get("en", key))
        return text.format(**kwargs) if kwargs else text
