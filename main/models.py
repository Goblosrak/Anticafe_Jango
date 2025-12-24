from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, verbose_name='Телефон', blank=True)
    date_of_birth = models.DateField(verbose_name='Дата рождения', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


class Zone(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название зоны')
    description = models.TextField(verbose_name='Описание')
    price_per_hour = models.IntegerField(verbose_name='Цена за час (руб.)')
    capacity = models.IntegerField(verbose_name='Вместимость (чел.)')

    def __str__(self):
        return self.title
    
    def get_available_seats(self):
        now = timezone.now()
        
        active_bookings = self.bookings.filter(
            status__in=['pending', 'confirmed'], 
            start_time__lte=now, 
            end_time__gte=now     
        )
        
        total_occupied_seats = sum(booking.number_of_people for booking in active_bookings)
        
        available_seats = max(0, self.capacity - total_occupied_seats)
        return available_seats
    
    def get_available_seats_for_time(self, start_time, end_time, exclude_booking_id=None):
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)
        
        overlapping_bookings = self.bookings.filter(
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exclude(status='cancelled') 
        
        if exclude_booking_id:
            overlapping_bookings = overlapping_bookings.exclude(id=exclude_booking_id)
        
        total_occupied_seats = sum(booking.number_of_people for booking in overlapping_bookings)
        
        return max(0, self.capacity - total_occupied_seats)
    
    def is_available_for_time(self, start_time, end_time, number_of_people=1, exclude_booking_id=None):
        """Проверяет, доступна ли зона на указанный интервал времени для указанного количества человек"""
        available_seats = self.get_available_seats_for_time(start_time, end_time, exclude_booking_id)
        return available_seats >= number_of_people
    
    def get_availability_status(self):
        """Возвращает статус доступности на текущий момент"""
        available_seats = self.get_available_seats()
        if available_seats == 0:
            return 'fully_booked'
        elif available_seats < self.capacity:
            return 'partially_available'
        else:
            return 'fully_available'
    
    class Meta:
        verbose_name = 'Зона'
        verbose_name_plural = 'Зоны'


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                             verbose_name='Пользователь', related_name='bookings')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, verbose_name='Зона', related_name='bookings')
    
    customer_name = models.CharField(max_length=100, verbose_name='Имя клиента')
    customer_phone = models.CharField(max_length=20, verbose_name='Телефон')
    customer_email = models.EmailField(verbose_name='Email')
    
    # Количество человек
    number_of_people = models.IntegerField(default=1, verbose_name='Количество человек')
    
    # Время бронирования
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    
    # Статус
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания брони')

    def __str__(self):
        return f"{self.customer_name} - {self.zone.title} ({self.start_time.strftime('%d.%m.%Y %H:%M')})"
    
    def get_duration_hours(self):
        """Возвращает продолжительность бронирования в часах"""
        duration = self.end_time - self.start_time
        return round(duration.total_seconds() / 3600, 1)
    
    def get_total_price(self):
        """Рассчитывает общую стоимость бронирования"""
        duration_hours = self.get_duration_hours()
        return int(duration_hours * self.zone.price_per_hour)
    
    def is_active_now(self):
        """Проверяет, активно ли бронирование в текущий момент"""
        now = timezone.now()
        
        # Убедимся, что времена в одном часовом поясе
        start_time = self.start_time
        end_time = self.end_time
        
        # Если время naive, делаем aware
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)
        
        # Проверяем, активно ли сейчас
        is_active = start_time <= now <= end_time and self.status in ['pending', 'confirmed']
        
        return is_active
    
    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']


class ContactMessage(models.Model):
    """Модель для хранения сообщений из формы обратной связи"""
    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    is_processed = models.BooleanField(default=False, verbose_name='Обработано')
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.created_at.strftime('%d.%m.%Y')}"
    
    class Meta:
        verbose_name = 'Сообщение обратной связи'
        verbose_name_plural = 'Сообщения обратной связи'
        ordering = ['-created_at']