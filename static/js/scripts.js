document.addEventListener('DOMContentLoaded', () => {
  console.log("Custom scripts loaded...");

  // 🔍 Live Search
  const setupSearch = (inputId) => {
    const searchInput = document.getElementById(inputId);
    if (searchInput) {
      searchInput.addEventListener("keyup", function () {
        const filter = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll("#studentTable tbody tr");
        rows.forEach(row => {
          const text = row.innerText.toLowerCase();
          row.style.display = text.includes(filter) ? "" : "none";
        });
      });
    }
  };

  setupSearch("studentSearchMain");
  setupSearch("studentSearchSecondary");

  // 🔃 Sorting
  const sortSelect = document.getElementById("studentSort");
  if (sortSelect) {
    sortSelect.addEventListener("change", function () {
      const sortKey = sortSelect.value;
      const rows = Array.from(document.querySelectorAll("#studentTable tbody tr"));

      rows.sort((a, b) => {
        const aVal = a.dataset[sortKey] || '';
        const bVal = b.dataset[sortKey] || '';
        return sortKey === "mark" ? parseFloat(bVal) - parseFloat(aVal) : aVal.localeCompare(bVal);
      });

      const tbody = document.querySelector("#studentTable tbody");
      tbody.innerHTML = "";
      rows.forEach(row => tbody.appendChild(row));
    });
  }

  // 👤 Profile Modal
  const profileModal = document.getElementById('profileModal');
  if (profileModal) {
    profileModal.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const dataType = button.getAttribute('data-type');
      const dataId = button.getAttribute('data-id');
      let url = '';

      if (dataType === 'student') {
        url = `/profile/student/${dataId}`;
      } else if (dataType === 'lecturer') {
        url = `/profile/lecturer/${dataId}`;
      }

      fetch(url)
        .then(response => response.json())
        .then(data => {
          // Common
          document.getElementById('profileName').textContent = data.full_name || data.name || '';
          document.getElementById('profilePhone').textContent = data.phone_number || '';
          document.getElementById('profileEmail').textContent = data.email || '';
          document.getElementById('profileNotes').textContent = data.notes || '';

          if (dataType === 'student') {
            document.getElementById('profileGroup').textContent = data.group || '';
            document.getElementById('profileLevel').textContent = data.level || '';
            document.getElementById('profileMark').textContent = data.mark || '';
            document.getElementById('profileCurrentModule').textContent = data.current_module || '';

            // Inventory usage
            const usageUl = document.getElementById('profileInventoryUsage');
            usageUl.innerHTML = '';
            (data.inventory_usage || []).forEach(u => {
              const li = document.createElement('li');
              li.textContent = `${u.date_issued}: Used ${u.quantity_used} of ${u.item_name}`;
              usageUl.appendChild(li);
            });

            // Mini tasks with Record Attempt button
            const tasksUl = document.getElementById('profileMiniTasks');
            tasksUl.innerHTML = '';
            (data.mini_tasks || []).forEach(t => {
              const li = document.createElement('li');
              li.innerHTML = `
                ${t.mini_task_title}
                (Attempt1=${t.attempt_1}, Attempt2=${t.attempt_2}, Attempt3=${t.attempt_3})
                <a href="/student_module_form/${t.mini_task_id}/${data.id}" class="btn btn-sm btn-outline-primary ms-2">Record</a>`;
              tasksUl.appendChild(li);
            });

            // Schedule
            const scheduleUl = document.getElementById('profileSchedule');
            scheduleUl.innerHTML = '';
            (data.schedule || []).forEach(s => {
              const li = document.createElement('li');
              li.textContent = `${s.start_time} to ${s.end_time} on ${s.machine}`;
              scheduleUl.appendChild(li);
            });
          } else {
            // Clear fields if lecturer
            ['Group', 'Level', 'Mark', 'CurrentModule', 'InventoryUsage', 'MiniTasks', 'Schedule']
              .forEach(id => document.getElementById(`profile${id}`).innerHTML = '');
          }
        })
        .catch(err => {
          console.error("Failed to load profile:", err);
        });
    });
  }
});


  