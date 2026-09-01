# Quick Start & Testing Guide

## ⚡ What Changed?

### 1. **Profile Pictures** 
- Users can upload profile pictures from their dashboard
- Pictures persist across logins
- Default color fallback shows user initials

### 2. **Role Validation on Login**
- System now validates that selected role matches user's registered role
- Prevents someone registered as "Student" from logging in as "Lecturer"

### 3. **Log Access for Lecturers**
- Lecturers only see supervisor-approved logs
- Logs are only visible for students assigned to them

---

## 🚀 How to Test

### Test 1: Profile Picture Upload (Student)
```
1. Login as Student with correct role
2. Click profile avatar in top right
3. Select "Customise Profile"
4. Upload a picture or choose color
5. Click "Save Changes"
6. Logout → Login again
7. ✓ Profile picture should still be there!
```

### Test 2: Role Validation
```
1. Go to login page
2. Select role "Lecturer" in dropdown
3. Enter Student credentials
4. Try to login
5. ✓ Should see error: "This account is registered as a Student..."
```

### Test 3: Different Colors for Each User
```
1. Login as Student → Choose color #FF5733
2. Logout
3. Login as Lecturer → Choose color #00AA00
4. Logout
5. Login as Student again
6. ✓ Color should still be #FF5733
7. Each role can have different profile colors!
```

### Test 4: Lecturer Log Visibility
```
1. Ensure a log is created and APPROVED by supervisor
2. Login as Lecturer
3. Check that:
   - ✓ Only students assigned to you are shown
   - ✓ Only approved logs show week links
   - ✓ Unapproved logs don't appear
```

### Test 5: Picture Persistence Across All Roles
```
1. Login as Student → Upload picture "photo1.jpg"
2. Logout
3. Login as Supervisor → Navigate to dashboard
4. ✓ Same picture shows in Supervisor avatar
5. Logout
6. Login as Lecturer → Navigate to dashboard
7. ✓ Same picture shows in Lecturer avatar
```

---

## 🔧 Implementation Details

### Files Changed:
1. ✅ **forms.py** - Added `ProfileUpdateForm`
2. ✅ **views.py** - Added role validation + profile update endpoint
3. ✅ **lecturer_dashboard.html** - Added profile settings modal
4. ✅ **student_dashboard.html** - Replaced localStorage with database
5. ✅ **supervisor_dashboard.html** - Already complete (no changes)

### Database Fields Used:
- `User.profile_photo` - ImageField for storing pictures
- `User.avatar_color` - CharField for storing hex colors

### API Endpoint:
- POST `/profile/update-meta/` - Saves profile changes

---

## ⚠️ Troubleshooting

**Issue**: Profile picture not showing
- **Check**: File was uploaded successfully (check media folder)
- **Check**: MEDIA_URL and MEDIA_ROOT settings in settings.py
- **Check**: User has refresh permission

**Issue**: Role validation not working
- **Check**: User model has `role` field
- **Check**: Login form includes role selector
- **Verify**: views.py has role comparison logic

**Issue**: Color not changing
- **Check**: avatarColorInput value is hex format (#XXXXXX)
- **Check**: Form data includes 'avatar_color' key
- **Verify**: Database saved the color (check User model)

---

## 📋 Requirements Met

✅ Profile picture support with default color
✅ User can choose/change profile color  
✅ User can upload profile picture from file
✅ Picture is saved and persists on next login
✅ Applied to Student, Lecturer, and Supervisor dashboards
✅ Role validation during login
✅ System declines if wrong role selected
✅ Logs only appear to lecturer after supervisor approval
✅ Logs only appear if lecturer is assigned

---

## 🎨 Color Picker

The color picker supports any hex color:
- Default: #0284c7 (Blue)
- Examples: #FF0000 (Red), #00FF00 (Green), #FFFF00 (Yellow)
- Use any online color picker to get hex values

---

## 📁 File Locations

- Settings: `core/settings.py`
- Forms: `core/forms.py`
- Views: `core/views.py`
- URLs: `core/urls.py`
- Templates: `templates/core/*.html`
- Media: `media/profile_photos/`

---

## 🔐 Security Notes

- ✅ CSRF protection on profile update
- ✅ File upload validated (accepts image/* only)
- ✅ Only authenticated users can upload
- ✅ Role validation prevents unauthorized access
- ✅ Users can only see their own profiles

---

## 🎯 Next Steps

1. Test all scenarios above
2. Verify images upload to media/profile_photos/
3. Check database for color and photo fields
4. Validate role selection on login
5. Monitor for any error messages
6. Celebrate! 🎉

---

## 📞 Support

If you encounter issues:
1. Check Django error logs
2. Verify CSRF token in forms
3. Check media folder permissions
4. Ensure ImageField is properly configured
5. Run: `python manage.py check`

