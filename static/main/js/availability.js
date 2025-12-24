class ZoneAvailability {
    constructor() {
        this.updateInterval = 30000; // 30 секунд
        this.init();
    }
    
    init() {
        this.updateAllZones();
        setInterval(() => this.updateAllZones(), this.updateInterval);
        
        // Обновляем при изменении времени в форме
        const timeInputs = document.querySelectorAll('#start_time, #end_time');
        timeInputs.forEach(input => {
            input.addEventListener('change', () => this.updateAllZones());
        });
    }
    
    async updateAllZones() {
        try {
            const response = await fetch('/zones/availability/');
            if (!response.ok) throw new Error('Network response was not ok');
            
            const zones = await response.json();
            
            zones.forEach(zone => {
                this.updateZoneCard(zone);
                this.updateZoneOption(zone);
            });
            
            console.log('Availability updated:', new Date().toLocaleTimeString());
        } catch (error) {
            console.error('Error updating availability:', error);
        }
    }
    
    updateZoneCard(zone) {
        const card = document.querySelector(`[data-zone-id="${zone.id}"]`);
        if (!card) return;
        
        // Обновляем информацию на карточке
        const seatsElement = card.querySelector('.available-seats');
        const statusElement = card.querySelector('.zone-status');
        const progressBar = card.querySelector('.progress-bar');
        
        if (seatsElement) {
            seatsElement.textContent = zone.available_seats;
            seatsElement.className = `available-seats ${this.getSeatsClass(zone)}`;
        }
        
        if (statusElement) {
            statusElement.textContent = this.getStatusText(zone);
            statusElement.className = `zone-status badge ${this.getStatusClass(zone)}`;
        }
        
        if (progressBar) {
            const percentage = (zone.available_seats / zone.capacity) * 100;
            progressBar.style.width = `${percentage}%`;
            progressBar.className = `progress-bar ${this.getProgressClass(zone)}`;
        }
    }
    
    updateZoneOption(zone) {
        const option = document.querySelector(`#zone option[value="${zone.id}"]`);
        if (!option) return;
        
        option.setAttribute('data-available', zone.available_seats);
        option.setAttribute('data-capacity', zone.capacity);
        option.textContent = `${zone.title} ${this.getOptionSuffix(zone)}`;
    }
    
    getSeatsClass(zone) {
        if (zone.available_seats === 0) return 'text-danger fw-bold';
        if (zone.available_seats < zone.capacity) return 'text-warning';
        return 'text-success';
    }
    
    getStatusClass(zone) {
        if (zone.available_seats === 0) return 'bg-danger';
        if (zone.available_seats < zone.capacity) return 'bg-warning text-dark';
        return 'bg-success';
    }
    
    getProgressClass(zone) {
        if (zone.available_seats === 0) return 'bg-danger';
        if (zone.available_seats < zone.capacity) return 'bg-warning';
        return 'bg-success';
    }
    
    getStatusText(zone) {
        if (zone.available_seats === 0) return 'Занято';
        if (zone.available_seats < zone.capacity) return 'Частично свободно';
        return 'Свободно';
    }
    
    getOptionSuffix(zone) {
        if (zone.available_seats === 0) return ' (Занято)';
        if (zone.available_seats < zone.capacity) return ` (${zone.available_seats} из ${zone.capacity} свободно)`;
        return ' (Свободно)';
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new ZoneAvailability();
});