# Admin Dynamic Group Selection Feature

## Overview
The Admin Dashboard now supports **dynamic multi-select group assignment** that automatically loads groups from your actual projects, accounts, and products defined in `projects.json`.

## Key Features

### 1. **Dynamic Group Loading**
- Groups are automatically extracted from `projects.json`
- Includes all unique groups from projects, accounts, and products
- Always includes "All" group for admin full access
- Syncs automatically when projects.json is updated

### 2. **Multi-Select Capability**
- Admins can assign users to **one or more groups**
- Checkbox-based interface for easy selection
- Visual indication showing number of items in each group
- Example: `Elanco (12 items)`, `CHOP (8 items)`

### 3. **Smart Group Storage**
- Multiple groups stored as comma-separated values: `"Elanco,CHOP,Microsoft"`
- Single group stored as single value: `"Elanco"`
- Backend API handles both formats seamlessly

### 4. **RBAC Filtering Integration**
- Users with multiple groups see combined data from all their groups
- Example: User with `Elanco,CHOP` sees all Elanco + CHOP projects/accounts
- "All" group provides access to everything (Admin only)

## How It Works

### Backend (api.py)
```python
GET /api/projects
```
Returns all projects, accounts, and products with their group assignments.

### Frontend (admin.html)

#### 1. Load Groups Function
```javascript
async function loadAvailableGroups() {
    // Fetches /api/projects
    // Extracts unique groups from all items
    // Builds group objects with metadata
}
```

#### 2. Populate Checkboxes
```javascript
function populateGroupCheckboxes(currentGroups) {
    // Parses comma-separated current groups
    // Creates checkbox for each available group
    // Shows item count per group
    // Pre-selects user's current groups
}
```

#### 3. Form Submission
```javascript
// Collects all checked boxes
const selectedGroups = Array.from(checkboxes).map(cb => cb.value);
const group = selectedGroups.join(',');
```

### Validation Rules
1. **At least one group required** - Users must have at least one group assigned
2. **"All" is Admin-only** - Only Admin role can have the "All" group
3. **Multi-group allowed** - Any combination of groups is permitted

## Usage Example

### Assigning Groups to a User

1. **Open Admin Dashboard**: Navigate to `http://localhost:8000/admin.html`
2. **Click Edit** on any user
3. **Group Selection Section** shows:
   ```
   ☑ All (24 items)
   ☐ Elanco (12 items)
   ☐ CHOP (8 items)
   ☐ Microsoft (4 items)
   ☐ Other (2 items)
   ```
4. **Select multiple groups** by checking boxes
5. **Click Save Changes**

### Result
- User's `Group` field in `users.xlsx` is updated: `"Elanco,CHOP"`
- User can now see projects/accounts from both Elanco and CHOP groups
- Main dashboard automatically filters content based on these groups

## projects.json Structure

Each item in projects.json must have a `group` field:

```json
{
  "projects": [
    {
      "id": "proj1",
      "name": "Unnamed Project",
      "group": "All",
      "type": "project"
    }
  ],
  "accounts": [
    {
      "id": "acc1", 
      "name": "Elanco",
      "group": "Elanco",
      "type": "account"
    },
    {
      "id": "acc2",
      "name": "CHOP",
      "group": "CHOP",
      "type": "account"
    }
  ],
  "products": [
    {
      "id": "prod1",
      "name": "Peets",
      "group": "Other",
      "type": "product"
    }
  ]
}
```

## Benefits

### 1. **Automatic Synchronization**
- No need to manually update group dropdowns
- Adding new projects automatically creates new group options
- Removes stale groups when projects are deleted

### 2. **Flexible Access Control**
- Assign users to specific projects/accounts
- Grant multi-project access easily
- Segregate contributors by client groups

### 3. **Better User Experience**
- Clear visibility of what's in each group
- Easy multi-selection with checkboxes
- Visual feedback with item counts

### 4. **Scalability**
- Works with any number of groups
- Handles complex project structures
- Scrollable interface for many groups (max-height: 300px)

## Technical Details

### CSS Styling
```css
.checkbox-group {
    max-height: 300px;
    overflow-y: auto;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    background: #fafafa;
}

.checkbox-item {
    display: flex;
    align-items: center;
    padding: 10px;
    margin-bottom: 8px;
    transition: background 0.2s;
}

.checkbox-item:hover {
    background: #f0f0f0;
}
```

### Group Parsing Logic
```javascript
// Frontend parses groups
const selectedGroups = currentGroups 
    ? currentGroups.split(',').map(g => g.trim()) 
    : [];

// Backend receives comma-separated string
{
  "target_email": "user@example.com",
  "role": "User",
  "group": "Elanco,CHOP,Microsoft"
}
```

### RBAC Filtering (index.html)
```javascript
function loadProjects() {
    const userGroup = userData.group; // "Elanco,CHOP"
    const userGroups = userGroup ? userGroup.split(',').map(g => g.trim()) : [];
    
    // Filter projects
    const filteredProjects = allProjects.filter(project => {
        if (userGroups.includes('All')) return true;
        if (!project.group) return userGroups.includes('All');
        return userGroups.includes(project.group);
    });
}
```

## Testing Instructions

### Test Case 1: Single Group Assignment
1. Edit user `niltripathy5@gmail.com`
2. Select only `Elanco` checkbox
3. Save changes
4. Login as that user
5. **Expected**: See only Elanco account and projects with group="Elanco" or group="All"

### Test Case 2: Multi-Group Assignment
1. Edit user `niltripathy5@gmail.com`
2. Select `Elanco` and `CHOP` checkboxes
3. Save changes
4. Login as that user
5. **Expected**: See Elanco + CHOP accounts and their associated projects

### Test Case 3: Admin with "All" Group
1. Edit admin user
2. Select only `All` checkbox
3. Save changes
4. Login as admin
5. **Expected**: See all projects, accounts, and products

### Test Case 4: Group Validation
1. Edit a user with role="User"
2. Try to select only "All" checkbox
3. **Expected**: Error message "Only Admin role can have 'All' group"

### Test Case 5: Dynamic Group Updates
1. Add new account to `projects.json`: `{ "name": "NewClient", "group": "NewClient" }`
2. Refresh admin dashboard
3. Edit any user
4. **Expected**: "NewClient" checkbox appears in group selection

## Troubleshooting

### Groups Not Loading
- **Check**: Backend server is running on port 8000
- **Check**: `/api/projects` endpoint is accessible
- **Check**: Browser console for errors
- **Fix**: Restart backend server

### Incorrect Filtering
- **Check**: User's Group field in users.xlsx has correct comma-separated values
- **Check**: projects.json has group field for all items
- **Check**: Browser console for RBAC filtering logs: `[RBAC] User Role: ... Group: ...`
- **Fix**: Update user's group via admin dashboard

### Checkboxes Not Appearing
- **Check**: CSS for `.checkbox-group` and `.checkbox-item` is present
- **Check**: `populateGroupCheckboxes()` function is called in `editUser()`
- **Check**: Browser console for JavaScript errors
- **Fix**: Clear browser cache and reload

### Multiple Groups Not Working
- **Check**: Form submission collects all checked boxes
- **Check**: Backend receives comma-separated string
- **Check**: RBAC filtering splits groups correctly
- **Fix**: Review form submit handler in admin.html

---

## Automatic Group Assignment (New Feature)

### Auto-Assignment When Contributors Create Projects

When a Contributor user creates a new project or account, the system automatically:

1. **Sets Project Group**: The project's `group` field is set to match the project name
   ```json
   {
     "name": "HPE",
     "group": "HPE",  // Auto-assigned
     "created_by": "contributor@example.com"
   }
   ```

2. **Updates Creator's Groups**: The new group is automatically added to the creator's profile
   ```
   Before: Group = "Peets,CHOP"
   After:  Group = "Peets,CHOP,HPE"
   ```

3. **Backend Implementation** (`api.py`):
   ```python
   # In create_project() endpoint
   new_project["group"] = project.name  # Auto-set group
   
   if project.creator_role != 'Admin':
       from auth import auth_service
       auth_service.add_group_to_user(creator_email, project.name)
   ```

4. **Frontend Refresh** (`index.html`):
   ```javascript
   await createProject(projectData);
   await Auth.validateSession();  // Refreshes user groups from Excel
   await loadProjects();          // Reload project list with new group
   ```

### Session Group Refresh Mechanism

The system now refreshes user groups on every session validation:

**Backend (`auth.py`):**
```python
def validate_session(self, session_token: str):
    # Validate session token
    session = SESSIONS.get(session_token)
    
    # Refresh user data from Excel
    email = session.get('email')
    if email:
        user = self.get_user_by_email(email)  # Read from Excel
        if user:
            session['group'] = user.get('Group')  # Update with latest
            session['role'] = user.get('Role')
            SESSIONS[session_token] = session  # Save to memory
    
    return session
```

**Benefits:**
- User permissions update immediately when admin changes their groups
- Contributors automatically get access to projects they create
- No manual intervention needed for group assignment
- Seamless user experience

### Testing Auto-Assignment

**Test Case: Contributor Creates Project**
1. Login as Contributor user with Group = "Peets"
2. Create new project named "HPE"
3. **Expected Behavior**:
   - Project created with `group: "HPE"`
   - User's Group updated to "Peets,HPE" in users.xlsx
   - Session refreshed automatically
   - HPE appears in user's project dropdown immediately

**Test Case: Admin Creates Project**
1. Login as Admin user
2. Create new project named "Microsoft"
3. **Expected Behavior**:
   - Project created with `group: "Microsoft"`
   - Admin's Group remains "All" (no change)
   - Project appears for all users with appropriate groups

### Monitoring Auto-Assignment

**Check users.xlsx:**
```excel
Before contributor creates "HPE":
Email: contributor@example.com | Group: Peets,CHOP

After creating "HPE":
Email: contributor@example.com | Group: Peets,CHOP,HPE
```

**Check projects.json:**
```json
{
  "id": "generated-id",
  "name": "HPE",
  "group": "HPE",  // Automatically set
  "created_by": "contributor@example.com",
  "type": "project"
}
```

---

## Future Enhancements

### Possible Improvements
1. **Group Management UI**: Add/edit/delete groups from admin dashboard
2. **Hierarchical Groups**: Support parent-child group relationships
3. **Group Permissions**: Fine-grained permissions per group (read/write/delete)
4. **User Group Analytics**: Show group usage statistics
5. **Bulk Group Assignment**: Select multiple users and assign groups at once
6. **Group Color Coding**: Visual distinction for different groups

### Migration Path
If you need to add new groups:
1. Update `projects.json` with new group names
2. Reload admin dashboard (groups auto-update)
3. Assign users to new groups via edit modal

## Security Considerations

### Access Control
- ✅ Only Admin role can access admin dashboard
- ✅ Session validation on every page load
- ✅ Backend validates all group assignments
- ✅ "All" group restricted to Admin role only

### Data Validation
- ✅ At least one group required
- ✅ Role-group combination validated
- ✅ Comma-separated format enforced
- ✅ XSS protection via proper HTML escaping

## Conclusion

The dynamic group selection feature provides a **scalable, maintainable, and user-friendly** approach to managing user access control. By automatically syncing with your actual project structure, it eliminates manual maintenance and reduces the risk of stale or incorrect group assignments.

**Key Takeaway**: Groups are no longer hardcoded—they're dynamically sourced from your project data, ensuring consistency across your ETL framework.
