document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const response = await fetch('/register/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });
    const result = await response.json();
    alert(`Registered: ${result.username}`);
});

document.getElementById('project-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('project-name').value;
    const response = await fetch('/projects/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
    });
    const result = await response.json();
    alert(`Project Created: ${result.name}`);
});

document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const projectId = document.getElementById('project-id').value;
    const fileInput = document.getElementById('document');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const response = await fetch(`/projects/${projectId}/documents/`, {
        method: 'POST',
        body: formData,
    });
    const result = await response.json();
    alert(`Document Uploaded: ${result.filename}`);
});

document.getElementById('extract-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const projectId = document.getElementById('extract-project-id').value;
    const response = await fetch(`/projects/${projectId}/extract_entities/`, {
        method: 'POST',
    });
    const result = await response.json();
    document.getElementById('entities-output').textContent = JSON.stringify(result, null, 2);
});
