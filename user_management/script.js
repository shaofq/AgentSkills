// script.js
let users = JSON.parse(localStorage.getItem('users')) || [];

function renderUsers() {
    const tableBody = document.getElementById('userTableBody');
    tableBody.innerHTML = '';
    
    users.forEach((user, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.phone || '未提供'}</td>
            <td>
                <button class="delete-btn" onclick="deleteUser(${index})">删除</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function addUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    
    // 简单验证
    if (!username || !email) {
        alert('用户名和邮箱是必填项！');
        return;
    }
    
    // 检查用户名是否已存在
    if (users.some(user => user.username === username)) {
        alert('用户名已存在！');
        return;
    }
    
    // 检查邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('请输入有效的邮箱地址！');
        return;
    }
    
    users.push({
        username: username,
        email: email,
        phone: phone || ''
    });
    
    localStorage.setItem('users', JSON.stringify(users));
    renderUsers();
    
    // 重置表单
    document.getElementById('userForm').reset();
}

function deleteUser(index) {
    if (confirm('确定要删除这个用户吗？')) {
        users.splice(index, 1);
        localStorage.setItem('users', JSON.stringify(users));
        renderUsers();
    }
}

// 初始化
document.getElementById('userForm').addEventListener('submit', addUser);
renderUsers();