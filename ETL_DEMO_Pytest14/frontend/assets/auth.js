// Authentication Module for WinETL InfinityX
// Handles session management, authentication checks, and user context

const Auth = {
    API_BASE: window.location.origin,
    
    // Check if user is logged in
    isAuthenticated() {
        const token = localStorage.getItem('sessionToken');
        return token !== null;
    },
    
    // Get current session token
    getToken() {
        return localStorage.getItem('sessionToken');
    },
    
    // Get current user data
    getUserData() {
        const userData = localStorage.getItem('userData');
        return userData ? JSON.parse(userData) : null;
    },
    
    // Validate session with server
    async validateSession() {
        const token = this.getToken();
        if (!token) return false;
        
        try {
            const response = await fetch(`${this.API_BASE}/api/auth/validate`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update stored user data
                localStorage.setItem('userData', JSON.stringify(data.user));
                return true;
            } else {
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Session validation error:', error);
            return false;
        }
    },
    
    // Logout user
    logout() {
        const token = this.getToken();
        
        // Call logout API
        if (token) {
            fetch(`${this.API_BASE}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }).catch(err => console.error('Logout error:', err));
        }
        
        // Clear local storage
        localStorage.removeItem('sessionToken');
        localStorage.removeItem('userData');
        
        // Redirect to login
        window.location.href = 'login.html';
    },
    
    // Check authentication and redirect if needed
    async requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = 'login.html';
            return false;
        }
        
        const valid = await this.validateSession();
        if (!valid) {
            window.location.href = 'login.html';
            return false;
        }
        
        return true;
    },
    
    // Initialize authentication UI
    initAuthUI() {
        const user = this.getUserData();
        if (!user) return;
        
        // Update user info in header
        const headerStatus = document.querySelector('.header-status');
        if (headerStatus) {
            const roleColor = user.Role === 'Admin' ? '#2ecc71' : user.Role === 'Contributor' ? '#f39c12' : '#3498db';
            
            headerStatus.innerHTML = `
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="text-align: right; line-height: 1.4;">
                        <div style="font-weight: 700; color: #333; font-size: 0.95em;">
                            <i class="fas fa-user-circle" style="color: ${roleColor}; margin-right: 5px;"></i>
                            ${user.username || user.UserName || 'User'}
                        </div>
                        <div style="font-size: 0.8em; color: #666;">
                            <span style="background: ${roleColor}; color: white; padding: 2px 8px; border-radius: 10px; font-weight: 600;">
                                ${user.role || user.Role || 'User'}
                            </span>
                            ${user.group || user.Group ? `<span style="margin-left: 5px; color: #888;">| ${user.group || user.Group}</span>` : ''}
                        </div>
                    </div>
                    ${user.role === 'Admin' || user.Role === 'Admin' ? `
                        <button onclick="window.location.href='admin.html'" 
                                style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                       color: white; border: none; padding: 8px 15px; border-radius: 8px; 
                                       cursor: pointer; font-weight: 600; font-size: 0.85em;
                                       transition: all 0.3s;">
                            <i class="fas fa-users-cog"></i> Admin
                        </button>
                    ` : ''}
                    <button onclick="Auth.logout()" 
                            style="background: #e74c3c; color: white; border: none; 
                                   padding: 8px 15px; border-radius: 8px; cursor: pointer; 
                                   font-weight: 600; font-size: 0.85em;
                                   transition: all 0.3s;">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </button>
                </div>
            `;
        }
    },
    
    // Apply RBAC filtering to data
    filterByPermissions(items, groupKey = 'group') {
        const user = this.getUserData();
        if (!user) return [];
        
        const role = user.role || user.Role || '';
        const group = user.group || user.Group || '';
        
        // Admin sees everything
        if (role === 'Admin' || group === 'All') {
            return items;
        }
        
        // Filter by group
        return items.filter(item => {
            const itemGroup = item[groupKey] || item[groupKey.charAt(0).toUpperCase() + groupKey.slice(1)] || '';
            return itemGroup === group;
        });
    },
    
    // Add authorization header to fetch requests
    async fetch(url, options = {}) {
        const token = this.getToken();
        
        if (!options.headers) {
            options.headers = {};
        }
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }
        
        return fetch(url, options);
    }
};

// Initialize authentication on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Skip auth for login and signup pages
    if (window.location.pathname.includes('login.html') || 
        window.location.pathname.includes('signup.html')) {
        return;
    }
    
    // Check authentication
    const authenticated = await Auth.requireAuth();
    
    if (authenticated) {
        // Initialize auth UI
        Auth.initAuthUI();
        
        console.log('%c✓ Authentication validated', 'color: #2ecc71; font-weight: bold;');
        console.log('User:', Auth.getUserData());
    }
});
