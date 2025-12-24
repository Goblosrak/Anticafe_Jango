from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Zone, Booking, UserProfile, ContactMessage
from django.utils import timezone

# Inline для профиля пользователя
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Дополнительная информация'
    fields = ['phone', 'date_of_birth']

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'booking_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    def booking_count(self, obj):
        """Количество бронирований пользователя"""
        return Booking.objects.filter(user=obj).count()
    booking_count.short_description = 'Бронирований'

# Регистрация в админке
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'date_of_birth', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('created_at',)

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'price_per_hour', 'capacity', 'current_available_seats', 'availability_status', 'booking_count')
    list_filter = ('capacity',)
    search_fields = ('title', 'description')
    readonly_fields = ('current_available_seats', 'availability_status', 'booking_count')
    
    def current_available_seats(self, obj):
        """Показывает свободные места на текущий момент"""
        return f"{obj.get_available_seats()}/{obj.capacity}"
    current_available_seats.short_description = 'Свободно/Всего'
    
    def availability_status(self, obj):
        """Показывает статус доступности"""
        status = obj.get_availability_status()
        if status == 'fully_booked':
            return '❌ Занято'
        elif status == 'partially_available':
            return '⚠️ Частично свободно'
        else:
            return '✅ Свободно'
    availability_status.short_description = 'Статус'
    
    def booking_count(self, obj):
        """Количество бронирований для этой зоны"""
        return obj.bookings.count()
    booking_count.short_description = 'Бронирований'

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at_display', 'is_processed', 'preview_message')
    list_filter = ('is_processed', 'created_at')
    list_editable = ('is_processed',)
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = 'Дата отправки'
    
    def preview_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    preview_message.short_description = 'Сообщение'
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'{updated} сообщений помечены как обработанные')
    mark_as_processed.short_description = 'Пометить как обработанные'
    
    def mark_as_unprocessed(self, request, queryset):
        updated = queryset.update(is_processed=False)
        self.message_user(request, f'{updated} сообщений помечены как необработанные')
    mark_as_unprocessed.short_description = 'Пометить как необработанные'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_email', 'zone_display', 'user_display', 
                    'start_time_display', 'end_time_display', 'status', 'total_price', 
                    'is_active_now', 'created_at_display')
    list_filter = ('status', 'zone', 'start_time', 'created_at', 'user')
    search_fields = ('customer_name', 'customer_phone', 'customer_email', 'zone__title', 'user__username')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'total_price_display', 'duration_display', 'is_active_now_display')
    date_hierarchy = 'created_at'
    actions = ['confirm_selected', 'cancel_selected', 'mark_as_pending', 'mark_as_completed']
    
    # Методы для красивого отображения
    def zone_display(self, obj):
        return obj.zone.title
    zone_display.short_description = 'Зона'
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.get_full_name()})"
        return "Гость"
    user_display.short_description = 'Пользователь'
    
    def start_time_display(self, obj):
        return obj.start_time.strftime('%d.%m.%Y %H:%M')
    start_time_display.short_description = 'Начало'
    
    def end_time_display(self, obj):
        return obj.end_time.strftime('%d.%m.%Y %H:%M')
    end_time_display.short_description = 'Окончание'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = 'Создано'
    
    def is_active_now(self, obj):
        return '✅' if obj.is_active_now() else '❌'
    is_active_now.short_description = 'Активно сейчас'
    
    def total_price(self, obj):
        return f"{obj.get_total_price()} руб."
    total_price.short_description = 'Стоимость'
    
    # Поля для просмотра
    def total_price_display(self, obj):
        return f"{obj.get_total_price()} руб."
    total_price_display.short_description = 'Общая стоимость'
    
    def duration_display(self, obj):
        return f"{obj.get_duration_hours()} ч."
    duration_display.short_description = 'Продолжительность'
    
    def is_active_now_display(self, obj):
        if obj.is_active_now():
            return "✅ Да, активно в данный момент"
        else:
            now = timezone.now()
            if now < obj.start_time:
                hours_to_start = int((obj.start_time - now).total_seconds() // 3600)
                return f"⏳ Еще не началось (через {hours_to_start} ч.)"
            elif now > obj.end_time:
                hours_ago = int((now - obj.end_time).total_seconds() // 3600)
                return f"⏰ Завершено ({hours_ago} ч. назад)"
            else:
                return "❌ Не активно (возможно, статус не 'подтверждено')"
    is_active_now_display.short_description = 'Текущий статус'
    
    # Групповые действия
    def confirm_selected(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} бронирований подтверждено')
    confirm_selected.short_description = 'Подтвердить выбранные'
    
    def cancel_selected(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} бронирований отменено')
    cancel_selected.short_description = 'Отменить выбранные'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} бронирований помечены как "ожидание"')
    mark_as_pending.short_description = 'Вернуть в ожидание'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} бронирований отмечены как завершенные')
    mark_as_completed.short_description = 'Отметить как завершенные'
    
    # Дополнительная информация в админке
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'user'),
            'classes': ('wide',)
        }),
        ('Детали бронирования', {
            'fields': ('zone', 'start_time', 'end_time', 'status'),
            'classes': ('wide',)
        }),
        ('Расчеты', {
            'fields': ('total_price_display', 'duration_display'),
            'classes': ('collapse',)
        }),
        ('Текущий статус', {
            'fields': ('is_active_now_display',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# Кастомный заголовок админки
admin.site.site_header = 'Администрирование антикафе "Чилл"'
admin.site.site_title = 'Антикафе "Чилл"'
admin.site.index_title = 'Панель управления'