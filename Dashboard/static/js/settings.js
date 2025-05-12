// Instrument management for settings page

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('instrumentSettingsTable')) {
        loadInstruments();
        setupInstrumentHandlers();
    }
});

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
