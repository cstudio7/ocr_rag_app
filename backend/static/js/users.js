// User Management JavaScript

class UserManager {
    constructor() {
        this.modal = document.getElementById('userModal');
        this.form = document.getElementById('userForm');
        this.usersTableBody = document.getElementById('usersTableBody');
        
        this.initializeEventListeners();
        this.loadUsers();
    }

    initializeEventListeners() {
        // Add user button
        document.getElementById('addUserBtn').addEventListener('click', () => {
            this.showModal();
        });

        // Close modal buttons
        document.getElementById('closeModal').addEventListener('click', () => {
            this.hideModal();
        });
        
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.hideModal();
        });

        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveUser();
        });

        // Close modal when clicking outside
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hideModal();
            }
        });
    }

    async loadUsers() {
        try {
            const response = await fetch('/api/users');
            const data = await response.json();
            
            if (data.error) {
                this.showError('Failed to load users: ' + data.error);
                return;
            }

            this.renderUsers(data.users);
            this.updateStats(data.stats);
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Failed to load users');
        }
    }

    renderUsers(users) {
        this.usersTableBody.innerHTML = '';
        
        users.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <div class="h-10 w-10 rounded-full bg-indigo-500 flex items-center justify-center">
                                <span class="text-sm font-medium text-white">${this.getInitials(user.first_name, user.last_name, user.username)}</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${user.username}</div>
                            <div class="text-sm text-gray-500">${user.email}</div>
                            <div class="text-sm text-gray-500">${user.first_name || ''} ${user.last_name || ''}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${this.getRoleBadgeClass(user.role)}">
                        ${user.role.toUpperCase()}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${user.last_login ? this.formatDate(user.last_login) : 'Never'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${this.formatDate(user.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="userManager.editUser(${user.id})" class="text-indigo-600 hover:text-indigo-900 mr-3">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="userManager.toggleUserStatus(${user.id}, ${user.is_active})" class="text-blue-600 hover:text-blue-900 mr-3">
                        <i class="fas fa-${user.is_active ? 'user-slash' : 'user-check'}"></i>
                    </button>
                    ${user.username !== 'admin' ? `
                        <button onclick="userManager.deleteUser(${user.id})" class="text-red-600 hover:text-red-900">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </td>
            `;
            this.usersTableBody.appendChild(row);
        });
    }

    updateStats(stats) {
        document.getElementById('totalUsers').textContent = stats.total_users;
        document.getElementById('activeUsers').textContent = stats.active_users;
        document.getElementById('adminUsers').textContent = stats.admin_users;
        document.getElementById('viewerUsers').textContent = stats.viewer_users;
    }

    getInitials(firstName, lastName, username) {
        if (firstName && lastName) {
            return (firstName.charAt(0) + lastName.charAt(0)).toUpperCase();
        } else if (firstName) {
            return firstName.charAt(0).toUpperCase();
        } else {
            return username.charAt(0).toUpperCase();
        }
    }

    getRoleBadgeClass(role) {
        switch (role) {
            case 'admin':
                return 'bg-red-100 text-red-800';
            case 'uploader':
                return 'bg-green-100 text-green-800';
            case 'viewer':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    showModal(user = null) {
        const modalTitle = document.getElementById('modalTitle');
        const passwordSection = document.getElementById('passwordSection');
        
        if (user) {
            modalTitle.textContent = 'Edit User';
            this.populateForm(user);
            passwordSection.querySelector('p').style.display = 'block';
        } else {
            modalTitle.textContent = 'Add User';
            this.form.reset();
            document.getElementById('userId').value = '';
            passwordSection.querySelector('p').style.display = 'none';
            document.getElementById('password').required = true;
        }
        
        this.modal.classList.remove('hidden');
    }

    hideModal() {
        this.modal.classList.add('hidden');
        this.form.reset();
    }

    populateForm(user) {
        document.getElementById('userId').value = user.id;
        document.getElementById('username').value = user.username;
        document.getElementById('email').value = user.email;
        document.getElementById('firstName').value = user.first_name || '';
        document.getElementById('lastName').value = user.last_name || '';
        document.getElementById('role').value = user.role;
        document.getElementById('password').required = false;
    }

    async saveUser() {
        const formData = new FormData(this.form);
        const userData = Object.fromEntries(formData.entries());
        
        const userId = userData.user_id;
        const isEdit = userId && userId !== '';
        
        try {
            const url = isEdit ? `/api/users/${userId}` : '/api/users';
            const method = isEdit ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            this.showSuccess(isEdit ? 'User updated successfully' : 'User created successfully');
            this.hideModal();
            this.loadUsers();
        } catch (error) {
            console.error('Error saving user:', error);
            this.showError('Failed to save user');
        }
    }

    async editUser(userId) {
        try {
            const response = await fetch(`/api/users/${userId}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError('Failed to load user: ' + data.error);
                return;
            }
            
            this.showModal(data.user);
        } catch (error) {
            console.error('Error loading user:', error);
            this.showError('Failed to load user');
        }
    }

    async toggleUserStatus(userId, currentStatus) {
        const action = currentStatus ? 'deactivate' : 'activate';
        
        if (!confirm(`Are you sure you want to ${action} this user?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/users/${userId}/toggle-status`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            this.showSuccess(`User ${action}d successfully`);
            this.loadUsers();
        } catch (error) {
            console.error('Error toggling user status:', error);
            this.showError('Failed to update user status');
        }
    }

    async deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            this.showSuccess('User deleted successfully');
            this.loadUsers();
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showError('Failed to delete user');
        }
    }

    showError(message) {
        // You can implement a toast notification system here
        alert('Error: ' + message);
    }

    showSuccess(message) {
        // You can implement a toast notification system here
        alert('Success: ' + message);
    }
}

// Initialize the user manager when the page loads
let userManager;
document.addEventListener('DOMContentLoaded', () => {
    userManager = new UserManager();
});
