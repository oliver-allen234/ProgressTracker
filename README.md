# Progress Tracker

A Django application for tracking personal goals and progress.

## User Roles and Permissions

### Admin vs. Regular Users

It is a common convention in applications like Progress Tracker to have a small number of admin users (often just one) and a larger number of regular users. This approach follows the principle of least privilege and provides several benefits:

#### Why Have Limited Admin Users?

1. **Security**: Limiting administrative access reduces the risk of accidental or malicious data manipulation
2. **Data Privacy**: Regular users can only see their own data, maintaining privacy between users
3. **Simplified User Experience**: Regular users see only what they need, making the interface cleaner and more focused
4. **Maintenance**: Admin users can help with system maintenance and user support without giving all users these capabilities

#### What Regular Users Can Do

Regular users in Progress Tracker can:
- Manage their personal goals and tasks
- Track their progress
- Log hours spent on goals
- View reports and statistics about their own activities

This functionality covers everything a typical user needs to track their personal progress effectively.

#### What Regular Users Cannot Do

Regular users cannot:
- Delete data (for data integrity)
- Access other users' information
- Modify system-wide settings or categories

These restrictions help maintain data integrity and user privacy.

#### When to Use Admin Capabilities

Admin capabilities should primarily be used for:
- System maintenance
- User support (helping users who are having issues)
- Managing global categories and settings
- Data cleanup when necessary

For more detailed information about permissions, see the [PERMISSIONS.md](PERMISSIONS.md) file.

## Getting Started

[Installation and setup instructions would go here]

## Features

- Goal tracking with categories
- Task management
- Progress updates
- Time logging
- Dashboard with statistics