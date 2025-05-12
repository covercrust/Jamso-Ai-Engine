// Instrument management for settings page

document.addEventListener('DOMContentLoaded', function() {
    // Instrument settings initialization
    if (document.getElementById('instrumentSettingsTable')) {
        loadInstruments();
        setupInstrumentHandlers();
    }
    
    // Profile settings initialization
    if (document.getElementById('profileForm')) {
        document.getElementById('profileForm').addEventListener('submit', function(e) {
            e.preventDefault();
            updateProfile();
        });
    }
});

// Profile update function
function updateProfile() {
    const formData = {
        email: document.getElementById('email').value,
        first_name: document.getElementById('first_name')?.value || '',
        last_name: document.getElementById('last_name')?.value || '',
        current_password: document.getElementById('current_password')?.value,
        new_password: document.getElementById('new_password')?.value,
        confirm_password: document.getElementById('confirm_password')?.value
    };
    
    // Check if password fields are filled
    if ((formData.new_password || formData.confirm_password) && !formData.current_password) {
        alert('Please enter your current password to change your password');
        return;
    }
    
    // Check if passwords match
    if (formData.new_password !== formData.confirm_password) {
        alert('New passwords do not match');
        return;
    }
    
    fetch('/dashboard/api/profile/update', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Profile updated successfully');
            // Clear password fields
            document.getElementById('current_password').value = '';
            document.getElementById('new_password').value = '';
            document.getElementById('confirm_password').value = '';
        } else {
            alert(data.message || 'Error updating profile');
        }
    })
    .catch(error => {
        console.error('Error updating profile:', error);
        alert('Error updating profile. Please try again.');
    });
}

function loadInstruments() {
    fetch('/dashboard/api/instruments')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderInstrumentTable(data.data);
            }
        });
}

function renderInstrumentTable(instruments) {
    const tbody = document.getElementById('instrumentSettingsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    instruments.forEach(instr => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${instr.name}</td>
            <td>${instr.risk_percent}%</td>
            <td>${instr.stop_loss}</td>
            <td>${instr.take_profit}</td>
            <td><span class="badge bg-${instr.enabled ? 'success' : 'secondary'}">${instr.enabled ? 'Enabled' : 'Disabled'}</span></td>
            <td>
                <button class="btn btn-sm btn-primary edit-instrument" data-id="${instr.id}">Edit</button>
                <button class="btn btn-sm btn-danger delete-instrument" data-id="${instr.id}">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function setupInstrumentHandlers() {
    document.getElementById('addInstrumentBtn')?.addEventListener('click', function() {
        // Show a modal or prompt for new instrument details
        const name = prompt('Instrument name:');
        if (!name) return;
        const risk = prompt('Risk %:');
        const sl = prompt('Stop Loss:');
        const tp = prompt('Take Profit:');
        fetch('/dashboard/api/instruments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, risk_percent: risk, stop_loss: sl, take_profit: tp, enabled: true })
        }).then(() => loadInstruments());
    });
    document.getElementById('instrumentSettingsTableBody')?.addEventListener('click', function(e) {
        if (e.target.classList.contains('edit-instrument')) {
            const id = e.target.dataset.id;
            const row = e.target.closest('tr');
            const name = prompt('Instrument name:', row.children[0].textContent);
            const risk = prompt('Risk %:', row.children[1].textContent.replace('%',''));
            const sl = prompt('Stop Loss:', row.children[2].textContent);
            const tp = prompt('Take Profit:', row.children[3].textContent);
            const enabled = confirm('Enable this instrument?');
            fetch(`/dashboard/api/instruments/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, risk_percent: risk, stop_loss: sl, take_profit: tp, enabled })
            }).then(() => loadInstruments());
        } else if (e.target.classList.contains('delete-instrument')) {
            const id = e.target.dataset.id;
            if (confirm('Delete this instrument?')) {
                fetch(`/dashboard/api/instruments/${id}`, { method: 'DELETE' })
                    .then(() => loadInstruments());
            }
        }
    });
}
