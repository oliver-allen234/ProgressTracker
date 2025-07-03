# Progress Tracker - User Roles and Permissions

This document outlines the permission structure for the Progress Tracker application, explaining what regular users and admin users can do.

## User Roles

The application has two main user roles:

1. **Regular Users** - Standard application users who can manage their own data
2. **Admin Users** - Users with administrative privileges who can manage all data in the system

## Regular User Capabilities

Regular users can:

- Create and manage their own profile
- Create, view, and update their own goals
- Create, view, and update their own tasks
- Mark their own tasks as complete/incomplete
- Log hours against their own goals
- Create progress updates for their own goals
- View dashboards and reports related to their own data

Regular users cannot:
- Delete goals or tasks (even their own)
- Access or modify other users' data
- Access the Django admin interface

## Admin User Capabilities

Admin users have all the capabilities of regular users, plus:

- Access the Django admin interface
- View, create, update, and delete any user's data
- Manage categories for the entire system
- Delete goals and tasks for any user
- View system-wide statistics and reports

## How Admin Status is Assigned

Admin status is assigned by setting the `is_staff` flag to `True` for a user. This can be done:

1. Through the Django admin interface by another admin
2. During user registration with a special parameter (for testing purposes only)
3. By directly modifying the database

## Implementation Details

The permission structure is implemented through:

1. Django's built-in permission system
2. Custom mixins in the application:
   - `AdminRequiredMixin`: Ensures only admin users can access certain views
   - `RegularUserMixin`: Ensures users can only access their own data

3. View-level permission checks that verify:
   - Object ownership (for regular users)
   - Admin status (for administrative operations)

## Best Practices

- Regular users should focus on tracking their own goals and progress
- Admin users should primarily use their elevated permissions for maintenance and support
- The application follows the principle of least privilege, where users only have access to what they need