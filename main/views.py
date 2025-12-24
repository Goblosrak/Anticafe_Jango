from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ContactForm
from .models import Zone, Booking, UserProfile, ContactMessage
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация прошла успешно.')
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'title': 'Регистрация',
        'form': form
    }
    return render(request, 'main/register.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    error = None
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                
                next_page = request.GET.get('next', 'profile')
                return redirect(next_page)
            else:
                error = 'Неверное имя пользователя или пароль'
        else:
            error = 'Неверное имя пользователя или пароль'
    else:
        form = CustomAuthenticationForm()
    
    context = {
        'title': 'Вход в систему',
        'form': form,
        'error': error
    }
    return render(request, 'main/login.html', context)


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('home')


@login_required
def profile_view(request):
    # Получаем или создаем профиль пользователя
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    recent_bookings = bookings[:5]
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if phone:
            profile.phone = phone
            profile.save()
            messages.success(request, 'Профиль успешно обновлен.')
        return redirect('profile')
    
    context = {
        'title': 'Личный кабинет',
        'profile': profile,
        'bookings': recent_bookings,
        'total_bookings': bookings.count(),
        'user': request.user
    }
    return render(request, 'main/profile.html', context)


@login_required
def booking_history_view(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'title': 'История бронирований',
        'bookings': bookings,
        'user': request.user
    }
    return render(request, 'main/booking_history.html', context)


def home(request):
    context = {
        'title': 'Главная'
    }
    return render(request, 'main/home.html', context)


def zones(request):
    zones_list = Zone.objects.all()
    
    # Добавляем информацию о доступных местах для каждой зоны
    for zone in zones_list:
        zone.available_seats = zone.get_available_seats()
        zone.availability_status = zone.get_availability_status()
    
    context = {
        'title': 'Наши зоны',
        'zones': zones_list
    }
    return render(request, 'main/zones.html', context)


def booking(request):
    zones_list = Zone.objects.all()
    
    if request.method == 'POST':
        try:
            print("Получен POST запрос на бронирование")
            
            # Получаем данные из формы
            zone_id = request.POST.get('zone')
            customer_name = request.POST.get('name')
            customer_phone = request.POST.get('phone')
            customer_email = request.POST.get('email')
            number_of_people = request.POST.get('number_of_people', 1)
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            print(f"Данные формы: zone_id={zone_id}, name={customer_name}, people={number_of_people}")
            
            # Проверяем, что все поля заполнены
            if not all([zone_id, customer_name, customer_phone, customer_email, start_time, end_time]):
                messages.error(request, 'Пожалуйста, заполните все поля формы.')
                print("Ошибка: не все поля заполнены")
                return render(request, 'main/booking.html', {
                    'title': 'Бронирование',
                    'zones': zones_list,
                    'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                })
            
            # Проверяем количество человек
            try:
                number_of_people = int(number_of_people)
                if number_of_people < 1:
                    messages.error(request, 'Количество человек должно быть не менее 1.')
                    return render(request, 'main/booking.html', {
                        'title': 'Бронирование',
                        'zones': zones_list,
                        'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                    })
            except (ValueError, TypeError):
                number_of_people = 1
            
            # Получаем объект зоны
            try:
                zone = Zone.objects.get(id=zone_id)
                print(f"Найдена зона: {zone.title}, вместимость: {zone.capacity}")
                
                # Проверяем, что количество человек не превышает вместимость зоны
                if number_of_people > zone.capacity:
                    messages.error(request, f'Выбрано {number_of_people} человек, но максимальная вместимость зоны "{zone.title}" - {zone.capacity} человек.')
                    return render(request, 'main/booking.html', {
                        'title': 'Бронирование',
                        'zones': zones_list,
                        'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                    })
                    
            except Zone.DoesNotExist:
                messages.error(request, 'Выбранная зона не найдена.')
                print(f"Ошибка: зона с ID {zone_id} не найдена")
                return render(request, 'main/booking.html', {
                    'title': 'Бронирование',
                    'zones': zones_list,
                    'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                })
            
            # Конвертируем строки в datetime
            start_datetime = parse_datetime(start_time)
            end_datetime = parse_datetime(end_time)
            
            if not start_datetime or not end_datetime:
                messages.error(request, 'Некорректный формат даты и времени.')
                print(f"Ошибка: некорректный формат времени start={start_time}, end={end_time}")
                return render(request, 'main/booking.html', {
                    'title': 'Бронирование',
                    'zones': zones_list,
                    'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                })
            
            print(f"Даты преобразованы: start={start_datetime}, end={end_datetime}")
            
            # Преобразуем naive datetime в aware
            current_tz = timezone.get_current_timezone()
            
            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime, current_tz)
            if timezone.is_naive(end_datetime):
                end_datetime = timezone.make_aware(end_datetime, current_tz)
            
            print(f"Даты с часовым поясом: start={start_datetime}, end={end_datetime}")
            
            # Теперь проверяем, что время начала не в прошлом
            if start_datetime < timezone.now():
                messages.error(request, 'Время начала не может быть в прошлом.')
                print(f"Ошибка: время начала в прошлом start={start_datetime}, now={timezone.now()}")
                return render(request, 'main/booking.html', {
                    'title': 'Бронирование',
                    'zones': zones_list,
                    'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                })
            
            # Проверяем, что время окончания позже времени начала
            if end_datetime <= start_datetime:
                messages.error(request, 'Время окончания должно быть позже времени начала.')
                print(f"Ошибка: время окончания раньше времени начала end={end_datetime}, start={start_datetime}")
                return render(request, 'main/booking.html', {
                    'title': 'Бронирование',
                    'zones': zones_list,
                    'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                })
            
            # Проверяем минимальное время бронирования (1 час)
            time_diff = (end_datetime - start_datetime).total_seconds() / 3600
            if time_diff < 1:
                messages.error(request, 'Минимальное время бронирования - 1 час.')
                print(f"Ошибка: время бронирования меньше 1 часа diff={time_diff}")
                return render(request, 'main/booking.html', {
                    'title': 'Бронирование',
                    'zones': zones_list,
                    'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                })
            
            # Проверяем доступность зоны на указанное время для указанного количества человек
            if not zone.is_available_for_time(start_datetime, end_datetime, number_of_people):
                messages.error(request, f'На выбранное время "{start_datetime.strftime("%d.%m.%Y %H:%M")}" в зоне "{zone.title}" недостаточно свободных мест для {number_of_people} человек.')
                print(f"Ошибка: зона недоступна для {number_of_people} человек на выбранное время")
                return render(request, 'main/booking.html', {
                    'title': 'Бронирование',
                    'zones': zones_list,
                    'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
                })
            
            # Создаем бронирование
            booking_obj = Booking.objects.create(
                zone=zone,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                number_of_people=number_of_people,
                start_time=start_datetime,
                end_time=end_datetime,
                status='confirmed'
            )
            
            print(f"Бронирование создано: ID={booking_obj.id}, человек: {number_of_people}")
            
            # Если пользователь авторизован, привязываем бронирование к нему
            if request.user.is_authenticated:
                booking_obj.user = request.user
                booking_obj.save()
                print(f"Бронирование привязано к пользователю: {request.user.username}")
            
            messages.success(request, 
                f'Бронирование успешно создано!<br>'
                f'<strong>Детали:</strong><br>'
                f'- Зона: {zone.title}<br>'
                f'- Количество человек: {number_of_people}<br>'
                f'- Время: {start_datetime.strftime("%d.%m.%Y %H:%M")} - {end_datetime.strftime("%H:%M")}<br>'
                f'- Стоимость: {booking_obj.get_total_price()} руб.<br>'
                f'<br>Бронирование подтверждено автоматически.'
            )
            
            print("Бронирование успешно завершено, редирект на страницу бронирования")
            return redirect('booking')
            
        except Exception as e:
            messages.error(request, f'Произошла ошибка при бронировании: {str(e)}')
            print(f"Критическая ошибка: {str(e)}")
    
    # Добавляем информацию о доступных местах
    for zone in zones_list:
        zone.available_seats = zone.get_available_seats()
    
    context = {
        'title': 'Бронирование',
        'zones': zones_list,
        'current_time': timezone.now().strftime('%Y-%m-%dT%H:%M')
    }
    return render(request, 'main/booking.html', context)


def contacts(request):
    if request.method == 'POST' and 'contact_name' in request.POST:
        form_data = {
            'name': request.POST.get('contact_name'),
            'email': request.POST.get('contact_email'),
            'message': request.POST.get('message')
        }
        
        form = ContactForm(form_data)
        
        if form.is_valid():
            contact_message = form.save()
            
            try:
                if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
                    send_mail(
                        subject=f'Новое сообщение от {contact_message.name}',
                        message=f"""
                        Имя: {contact_message.name}
                        Email: {contact_message.email}
                        Сообщение: {contact_message.message}
                        
                        Дата: {contact_message.created_at.strftime("%d.%m.%Y %H:%M")}
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.DEFAULT_FROM_EMAIL],
                        fail_silently=True,
                    )
                
                messages.success(request, 'Ваше сообщение успешно отправлено! Мы ответим вам в ближайшее время.')
                return redirect('contacts')
            
            except Exception as e:
                messages.warning(request, 'Сообщение сохранено, но произошла ошибка при отправке email.')
        
        else:
            # Если форма невалидна, показываем ошибки
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Ошибка в поле "{field}": {error}')
    else:
        form = ContactForm()
    
    context = {
        'title': 'Контакты',
        'form': form
    }
    return render(request, 'main/contacts.html', context)


# API для проверки доступности
def check_availability_api(request):
    """API для проверки доступности всех зон на текущий момент"""
    zones_data = []
    for zone in Zone.objects.all():
        available_seats = zone.get_available_seats()  
        
        zones_data.append({
            'id': zone.id,
            'title': zone.title,
            'capacity': zone.capacity,
            'available_seats': available_seats,
            'status': zone.get_availability_status(),
            'is_available': available_seats > 0,
            'updated_at': timezone.now().isoformat()
        })
    
    return JsonResponse({
        'zones': zones_data,
        'current_time': timezone.now().isoformat(),
        'success': True
    })

def check_zone_availability(request, zone_id=None):
    try:
        if request.method == 'GET':
            # Получаем параметры из GET запроса
            zone_id = request.GET.get('zone_id', zone_id)
            start_time_str = request.GET.get('start_time')
            end_time_str = request.GET.get('end_time')
            number_of_people = int(request.GET.get('number_of_people', 1))
            
            if not zone_id:
                return JsonResponse({'error': 'Не указан ID зоны'}, status=400)
            
            zone = Zone.objects.get(id=zone_id)
            
            if start_time_str and end_time_str:
                # Проверяем доступность на конкретный интервал времени
                start_time = parse_datetime(start_time_str)
                end_time = parse_datetime(end_time_str)
                
                if not start_time or not end_time:
                    return JsonResponse({'error': 'Некорректный формат времени'}, status=400)
                
                # Преобразуем naive datetime в aware
                current_tz = timezone.get_current_timezone()
                if timezone.is_naive(start_time):
                    start_time = timezone.make_aware(start_time, current_tz)
                if timezone.is_naive(end_time):
                    end_time = timezone.make_aware(end_time, current_tz)
                
                # Проверяем доступность
                available_seats = zone.get_available_seats_for_time(start_time, end_time)
                is_available = available_seats >= number_of_people
                
                return JsonResponse({
                    'zone_id': zone.id,
                    'zone_name': zone.title,
                    'available': is_available,
                    'available_seats': available_seats,
                    'requested_people': number_of_people,
                    'capacity': zone.capacity,
                    'status': 'available' if is_available else 'booked',
                    'message': f'Доступно {available_seats} мест' if is_available else f'Недостаточно мест. Доступно только {available_seats}',
                    'requested_start': start_time_str,
                    'requested_end': end_time_str,
                    'timestamp': timezone.now().isoformat()
                })
            else:
                available_seats = zone.get_available_seats()
                
                return JsonResponse({
                    'zone_id': zone.id,
                    'zone_name': zone.title,
                    'available_seats': available_seats,
                    'capacity': zone.capacity,
                    'status': zone.get_availability_status(),
                    'message': 'Занято' if available_seats == 0 else f'Свободно {available_seats} из {zone.capacity} мест',
                    'current_time': timezone.now().isoformat(),
                    'timestamp': timezone.now().isoformat()
                })
                
    except Zone.DoesNotExist:
        return JsonResponse({'error': 'Зона не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def debug_time_info(request):
    """Страница для отладки времени"""
    from datetime import datetime
    
    if request.method == 'POST' and request.POST.get('action') == 'create_test':
        try:
            zone = Zone.objects.first()
            if zone:
                now = timezone.now()
                booking = Booking.objects.create(
                    zone=zone,
                    customer_name="Тестовый клиент",
                    customer_phone="+79999999999",
                    customer_email="test@example.com",
                    number_of_people=2,
                    start_time=now - timedelta(minutes=30),
                    end_time=now + timedelta(minutes=30),
                    status='confirmed'
                )
                
                if request.user.is_authenticated:
                    booking.user = request.user
                    booking.save()
                
                messages.success(request, f"Создано тестовое бронирование ID {booking.id} на 2 человека")
        except Exception as e:
            messages.error(request, f"Ошибка: {str(e)}")
        return redirect('debug_time')
    
    context = {
        'title': 'Отладка времени',
        'timezone_now': timezone.now(),
        'timezone_now_local': timezone.localtime(timezone.now()),
        'datetime_now': datetime.now(),
        'current_timezone': timezone.get_current_timezone(),
    }
    
    bookings_info = []
    for booking in Booking.objects.all()[:10]:
        try:
            start_local = timezone.localtime(booking.start_time) if timezone.is_aware(booking.start_time) else booking.start_time
            end_local = timezone.localtime(booking.end_time) if timezone.is_aware(booking.end_time) else booking.end_time
        except:
            start_local = booking.start_time
            end_local = booking.end_time
            
        bookings_info.append({
            'id': booking.id,
            'zone': booking.zone.title,
            'start': booking.start_time,
            'end': booking.end_time,
            'people': booking.number_of_people,
            'status': booking.status,
            'is_active': booking.is_active_now(),
            'start_local': start_local,
            'end_local': end_local,
            'user': booking.user.username if booking.user else 'Гость'
        })
    
    context['bookings_info'] = bookings_info
    
    zones_info = []
    for zone in Zone.objects.all():
        zones_info.append({
            'zone': zone,
            'available_seats': zone.get_available_seats(),
            'capacity': zone.capacity,
            'status': zone.get_availability_status(),
        })
    
    context['zones_info'] = zones_info
    
    context['use_tz_setting'] = getattr(settings, 'USE_TZ', False)
    context['time_zone_setting'] = getattr(settings, 'TIME_ZONE', 'Не установлен')
    
    return render(request, 'main/debug_time.html', context)