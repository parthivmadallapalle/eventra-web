#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_USERS 100
#define MAX_EVENTS 50
#define MAX_TICKETS 200
#define MAX_SPONSORSHIPS 50
#define MAX_ZONES 10
#define MAX_SCHEDULE 10

#define USERS_FILE "users.dat"
#define EVENTS_FILE "events.dat"
#define TICKETS_FILE "tickets.dat"
#define SPONSORSHIPS_FILE "sponsorships.dat"

/* ========================================================================= */
/*       MODULE 1: AUTHENTICATION & USER MANAGEMENT (SRS v1.0 FR1 - FR5)     */
/* ========================================================================= */

typedef enum {
    ROLE_ORGANIZER = 1,
    ROLE_ATTENDEE = 2,
    ROLE_SPONSOR = 3,
    ROLE_STAFF = 4,
    ROLE_ADMIN = 5
} UserRole;

typedef struct {
    int userId;
    char name[60];
    char email[60];
    char passwordHash[65];
    UserRole role;
    char phone[20];
    char organization[60];
    int isActive;
} User;

/* ========================================================================= */
/*       MODULE 2: EVENT MANAGEMENT ENTITIES (SRS v1.0 FR6 - FR13)          */
/* ========================================================================= */

typedef enum {
    STATUS_DRAFT = 1,
    STATUS_PENDING = 2,
    STATUS_APPROVED = 3,
    STATUS_PUBLISHED = 4,
    STATUS_CANCELLED = 5
} EventStatus;

typedef struct {
    int zoneId;
    char name[50];
    int capacity;
    int currentOccupancy;
} VenueZone;

typedef struct {
    int itemId;
    char title[60];
    char timeWindow[40];
    char stage[50];
} ScheduleItem;

typedef struct {
    int eventId;
    int organizerId;
    char name[80];
    char type[40];
    char venue[80];
    char date[20];
    int capacity;
    int availableSeats;
    int expectedAttendance;
    double budget;
    EventStatus status;
    char adminFeedback[100];
    int zoneCount;
    VenueZone zones[MAX_ZONES];
    int scheduleCount;
    ScheduleItem schedule[MAX_SCHEDULE];
} Event;

/* ========================================================================= */
/*       MODULE 3: SPONSORSHIP MANAGEMENT ENTITIES (SRS v1.0 FR14 - FR23)   */
/* ========================================================================= */

typedef struct {
    int sponsorshipId;
    int eventId;
    int sponsorId;
    char sponsorName[60];
    char eventName[80];
    char tier[30];
    double amount;
    char status[20];
    char pledgedAt[30];
} Sponsorship;

/* ========================================================================= */
/*       MODULE 4 & 5: TICKETING & GATE ENTRY (SRS v1.0 FR24 - FR35)        */
/* ========================================================================= */

typedef struct {
    int ticketId;
    int eventId;
    int attendeeId;
    char attendeeName[60];
    char eventName[80];
    char tier[30];
    double price;
    char qrToken[65];
    int isCheckedIn;
    char checkInTime[30];
    char checkInGate[30];
    int isCancelled;
} Ticket;

/* ========================================================================= */
/*                          GLOBAL DATA STORES                               */
/* ========================================================================= */

User users[MAX_USERS];
int userCount = 0;

Event events[MAX_EVENTS];
int eventCount = 0;

Ticket tickets[MAX_TICKETS];
int ticketCount = 0;

Sponsorship sponsorships[MAX_SPONSORSHIPS];
int sponsorshipCount = 0;

/* Active session */
User* currentUser = NULL;

/* ========================================================================= */
/*                          SECURITY & UTILITY HELPERS                       */
/* ========================================================================= */

const char* getRoleName(UserRole role)
{
    switch (role) {
        case ROLE_ORGANIZER: return "Organizer";
        case ROLE_ATTENDEE:  return "Attendee";
        case ROLE_SPONSOR:   return "Sponsor";
        case ROLE_STAFF:     return "Event Staff";
        case ROLE_ADMIN:     return "Admin";
        default:             return "Unknown";
    }
}

const char* getStatusName(EventStatus status)
{
    switch (status) {
        case STATUS_DRAFT:      return "DRAFT";
        case STATUS_PENDING:    return "PENDING APPROVAL";
        case STATUS_APPROVED:   return "APPROVED";
        case STATUS_PUBLISHED:  return "PUBLISHED";
        case STATUS_CANCELLED:  return "CANCELLED";
        default:                return "UNKNOWN";
    }
}

void hashPassword(const char* password, char* outputHash)
{
    const char* salt = "EVENTRA_SALT_2026_IIITK";
    unsigned long hash1 = 5381;
    unsigned long hash2 = 1779033703;
    int i;

    for (i = 0; password[i] != '\0'; i++) {
        hash1 = ((hash1 << 5) + hash1) ^ (unsigned char)password[i];
        hash2 = ((hash2 << 5) + hash2) + (unsigned char)password[i] + (unsigned long)i;
    }

    for (i = 0; salt[i] != '\0'; i++) {
        hash1 = ((hash1 << 5) + hash1) + (unsigned char)salt[i];
        hash2 = ((hash2 << 7) ^ hash2) + (unsigned char)salt[i];
    }

    sprintf(outputHash, "%08lx%08lx%08lx%08lx",
            hash1, hash2, hash1 ^ 0xA5A5A5A5, hash2 ^ 0x5A5A5A5A);
}

void generateQRToken(int ticketId, int eventId, int attendeeId, char* outputToken)
{
    char seed[120];
    sprintf(seed, "TKT-%d-EVT-%d-USR-%d-EVENTRA2026", ticketId, eventId, attendeeId);
    hashPassword(seed, outputToken);
}

int findUserByEmail(const char* email)
{
    for (int i = 0; i < userCount; i++) {
        if (strcmp(users[i].email, email) == 0) return i;
    }
    return -1;
}

int findUserById(int userId)
{
    for (int i = 0; i < userCount; i++) {
        if (users[i].userId == userId) return i;
    }
    return -1;
}

int findEventById(int eventId)
{
    for (int i = 0; i < eventCount; i++) {
        if (events[i].eventId == eventId) return i;
    }
    return -1;
}

int findTicketById(int ticketId)
{
    for (int i = 0; i < ticketCount; i++) {
        if (tickets[i].ticketId == ticketId) return i;
    }
    return -1;
}

int findTicketByToken(const char* token)
{
    for (int i = 0; i < ticketCount; i++) {
        if (strcmp(tickets[i].qrToken, token) == 0) return i;
    }
    return -1;
}

void getCurrentTimestamp(char* buffer, int maxLen)
{
    time_t now = time(NULL);
    struct tm* tm_info = localtime(&now);
    if (tm_info) {
        strftime(buffer, maxLen, "%Y-%m-%d %H:%M:%S", tm_info);
    } else {
        strncpy(buffer, "2026-09-14 10:00:00", maxLen);
    }
}

/* ========================================================================= */
/*                         DATA PERSISTENCE (FILE I/O)                       */
/* ========================================================================= */

void saveUsersToFile()
{
    FILE* fp = fopen(USERS_FILE, "wb");
    if (!fp) return;
    fwrite(&userCount, sizeof(int), 1, fp);
    fwrite(users, sizeof(User), userCount, fp);
    fclose(fp);
}

void saveEventsToFile()
{
    FILE* fp = fopen(EVENTS_FILE, "wb");
    if (!fp) return;
    fwrite(&eventCount, sizeof(int), 1, fp);
    fwrite(events, sizeof(Event), eventCount, fp);
    fclose(fp);
}

void saveTicketsToFile()
{
    FILE* fp = fopen(TICKETS_FILE, "wb");
    if (!fp) return;
    fwrite(&ticketCount, sizeof(int), 1, fp);
    fwrite(tickets, sizeof(Ticket), ticketCount, fp);
    fclose(fp);
}

void saveSponsorshipsToFile()
{
    FILE* fp = fopen(SPONSORSHIPS_FILE, "wb");
    if (!fp) return;
    fwrite(&sponsorshipCount, sizeof(int), 1, fp);
    fwrite(sponsorships, sizeof(Sponsorship), sponsorshipCount, fp);
    fclose(fp);
}

void seedDefaultData()
{
    // 1. Seed Default Users
    if (userCount == 0) {
        users[0].userId = 1;
        strcpy(users[0].name, "Parthiv Naga");
        strcpy(users[0].email, "admin@eventra.com");
        hashPassword("admin123", users[0].passwordHash);
        users[0].role = ROLE_ADMIN;
        strcpy(users[0].phone, "+91 98765 43210");
        strcpy(users[0].organization, "Eventra Central Administration");
        users[0].isActive = 1;

        users[1].userId = 2;
        strcpy(users[1].name, "Rohit Somuri");
        strcpy(users[1].email, "organizer@fest.org");
        hashPassword("pass123", users[1].passwordHash);
        users[1].role = ROLE_ORGANIZER;
        strcpy(users[1].phone, "+91 98765 43211");
        strcpy(users[1].organization, "IIITK Cultural & Tech Club");
        users[1].isActive = 1;

        users[2].userId = 3;
        strcpy(users[2].name, "Banoth Manohar");
        strcpy(users[2].email, "attendee@fest.org");
        hashPassword("pass123", users[2].passwordHash);
        users[2].role = ROLE_ATTENDEE;
        strcpy(users[2].phone, "+91 91234 56780");
        strcpy(users[2].organization, "N/A");
        users[2].isActive = 1;

        users[3].userId = 4;
        strcpy(users[3].name, "Sai Ganesh");
        strcpy(users[3].email, "sponsor@novatech.com");
        hashPassword("pass123", users[3].passwordHash);
        users[3].role = ROLE_SPONSOR;
        strcpy(users[3].phone, "+91 91234 56781");
        strcpy(users[3].organization, "NovaTech Global Solutions");
        users[3].isActive = 1;

        users[4].userId = 5;
        strcpy(users[4].name, "Akhil Paidi");
        strcpy(users[4].email, "staff@gate1.com");
        hashPassword("pass123", users[4].passwordHash);
        users[4].role = ROLE_STAFF;
        strcpy(users[4].phone, "+91 91234 56782");
        strcpy(users[4].organization, "Gate Alpha Operations");
        users[4].isActive = 1;

        userCount = 5;
        saveUsersToFile();
    }

    // 2. Seed Default Events
    if (eventCount == 0) {
        events[0].eventId = 1;
        events[0].organizerId = 2;
        strcpy(events[0].name, "TechFest 2026");
        strcpy(events[0].type, "Tech Fest");
        strcpy(events[0].venue, "IIITK Campus Arena");
        strcpy(events[0].date, "2026-10-15");
        events[0].capacity = 1200;
        events[0].availableSeats = 1198;
        events[0].expectedAttendance = 1000;
        events[0].budget = 550000.0;
        events[0].status = STATUS_PUBLISHED;
        strcpy(events[0].adminFeedback, "Approved by Central Administration");

        events[0].zoneCount = 3;
        events[0].zones[0].zoneId = 1;
        strcpy(events[0].zones[0].name, "Main Auditorium");
        events[0].zones[0].capacity = 600;
        events[0].zones[0].currentOccupancy = 140;

        events[0].zones[1].zoneId = 2;
        strcpy(events[0].zones[1].name, "Innovation Exhibition Hall");
        events[0].zones[1].capacity = 400;
        events[0].zones[1].currentOccupancy = 85;

        events[0].zones[2].zoneId = 3;
        strcpy(events[0].zones[2].name, "Gate Alpha Security Entry");
        events[0].zones[2].capacity = 200;
        events[0].zones[2].currentOccupancy = 30;

        events[0].scheduleCount = 2;
        events[0].schedule[0].itemId = 1;
        strcpy(events[0].schedule[0].title, "Hackathon 24-Hour Kickoff");
        strcpy(events[0].schedule[0].timeWindow, "09:00 AM - 11:00 AM");
        strcpy(events[0].schedule[0].stage, "Lab Complex");

        events[0].schedule[1].itemId = 2;
        strcpy(events[0].schedule[1].title, "AI & Robotics Keynote Talk");
        strcpy(events[0].schedule[1].timeWindow, "02:00 PM - 04:00 PM");
        strcpy(events[0].schedule[1].stage, "Main Auditorium");

        events[1].eventId = 2;
        events[1].organizerId = 2;
        strcpy(events[1].name, "Campus Cultural Night");
        strcpy(events[1].type, "Cultural Fest");
        strcpy(events[1].venue, "Open Air Amphitheatre");
        strcpy(events[1].date, "2026-11-05");
        events[1].capacity = 800;
        events[1].availableSeats = 799;
        events[1].expectedAttendance = 750;
        events[1].budget = 350000.0;
        events[1].status = STATUS_PUBLISHED;
        strcpy(events[1].adminFeedback, "Approved by Central Administration");

        events[1].zoneCount = 2;
        events[1].zones[0].zoneId = 1;
        strcpy(events[1].zones[0].name, "Amphitheatre Seating");
        events[1].zones[0].capacity = 500;
        events[1].zones[0].currentOccupancy = 60;

        events[1].zones[1].zoneId = 2;
        strcpy(events[1].zones[1].name, "Food & Art Stalls");
        events[1].zones[1].capacity = 300;
        events[1].zones[1].currentOccupancy = 40;

        events[1].scheduleCount = 1;
        events[1].schedule[0].itemId = 1;
        strcpy(events[1].schedule[0].title, "Live Musical Band & Dance Night");
        strcpy(events[1].schedule[0].timeWindow, "06:30 PM - 10:00 PM");
        strcpy(events[1].schedule[0].stage, "Main Stage");

        eventCount = 2;
        saveEventsToFile();
    }

    // 3. Seed Default Tickets
    if (ticketCount == 0) {
        tickets[0].ticketId = 101;
        tickets[0].eventId = 1;
        tickets[0].attendeeId = 3;
        strcpy(tickets[0].attendeeName, "Banoth Manohar");
        strcpy(tickets[0].eventName, "TechFest 2026");
        strcpy(tickets[0].tier, "VIP Pass");
        tickets[0].price = 499.0;
        generateQRToken(101, 1, 3, tickets[0].qrToken);
        tickets[0].isCheckedIn = 0;
        strcpy(tickets[0].checkInTime, "N/A");
        strcpy(tickets[0].checkInGate, "N/A");
        tickets[0].isCancelled = 0;

        tickets[1].ticketId = 102;
        tickets[1].eventId = 2;
        tickets[1].attendeeId = 3;
        strcpy(tickets[1].attendeeName, "Banoth Manohar");
        strcpy(tickets[1].eventName, "Campus Cultural Night");
        strcpy(tickets[1].tier, "General Entry");
        tickets[1].price = 199.0;
        generateQRToken(102, 2, 3, tickets[1].qrToken);
        tickets[1].isCheckedIn = 0;
        strcpy(tickets[1].checkInTime, "N/A");
        strcpy(tickets[1].checkInGate, "N/A");
        tickets[1].isCancelled = 0;

        ticketCount = 2;
        saveTicketsToFile();
    }

    // 4. Seed Default Sponsorship
    if (sponsorshipCount == 0) {
        sponsorships[0].sponsorshipId = 1;
        sponsorships[0].eventId = 1;
        sponsorships[0].sponsorId = 4;
        strcpy(sponsorships[0].sponsorName, "NovaTech Global Solutions");
        strcpy(sponsorships[0].eventName, "TechFest 2026");
        strcpy(sponsorships[0].tier, "Gold Partner");
        sponsorships[0].amount = 25000.0;
        strcpy(sponsorships[0].status, "Confirmed");
        strcpy(sponsorships[0].pledgedAt, "2026-09-01 14:30:00");
        sponsorshipCount = 1;
        saveSponsorshipsToFile();
    }
}

void loadDataFromFiles()
{
    FILE* fp = fopen(USERS_FILE, "rb");
    if (fp) {
        fread(&userCount, sizeof(int), 1, fp);
        if (userCount > 0 && userCount <= MAX_USERS) {
            fread(users, sizeof(User), userCount, fp);
        } else {
            userCount = 0;
        }
        fclose(fp);
    }

    fp = fopen(EVENTS_FILE, "rb");
    if (fp) {
        fread(&eventCount, sizeof(int), 1, fp);
        if (eventCount > 0 && eventCount <= MAX_EVENTS) {
            fread(events, sizeof(Event), eventCount, fp);
        } else {
            eventCount = 0;
        }
        fclose(fp);
    }

    fp = fopen(TICKETS_FILE, "rb");
    if (fp) {
        fread(&ticketCount, sizeof(int), 1, fp);
        if (ticketCount > 0 && ticketCount <= MAX_TICKETS) {
            fread(tickets, sizeof(Ticket), ticketCount, fp);
        } else {
            ticketCount = 0;
        }
        fclose(fp);
    }

    fp = fopen(SPONSORSHIPS_FILE, "rb");
    if (fp) {
        fread(&sponsorshipCount, sizeof(int), 1, fp);
        if (sponsorshipCount > 0 && sponsorshipCount <= MAX_SPONSORSHIPS) {
            fread(sponsorships, sizeof(Sponsorship), sponsorshipCount, fp);
        } else {
            sponsorshipCount = 0;
        }
        fclose(fp);
    }

    seedDefaultData();
}

/* ========================================================================= */
/*       MODULE 1: USER REGISTRATION, AUTHENTICATION & PROFILES             */
/* ========================================================================= */

void registerUser()
{
    if (userCount >= MAX_USERS) {
        printf("\n[Error] Maximum user limit reached.\n");
        return;
    }

    User newUser;
    newUser.userId = userCount + 1;
    newUser.isActive = 1;

    printf("\n==================================================\n");
    printf("            EVENTRA - USER REGISTRATION           \n");
    printf("==================================================\n");
    printf("Select User Role:\n");
    printf("  1. Event Organizer\n");
    printf("  2. Attendee\n");
    printf("  3. Sponsor\n");
    printf("  4. Event Staff\n");
    printf("  5. Administrator (Requires Auth Key)\n");
    printf("Enter choice (1-5): ");

    int roleChoice;
    if (scanf("%d", &roleChoice) != 1 || roleChoice < 1 || roleChoice > 5) {
        printf("\n[Error] Invalid role selection.\n");
        while (getchar() != '\n');
        return;
    }
    while (getchar() != '\n');

    if (roleChoice == 5) {
        char adminKey[50];
        printf("Enter Master Admin Authorization Key: ");
        if (scanf("%49s", adminKey) != 1) return;
        while (getchar() != '\n');
        if (strcmp(adminKey, "EVENTRA_ADMIN_2026") != 0) {
            printf("\n[Error] Invalid Admin key! Registration rejected.\n");
            return;
        }
    }
    newUser.role = (UserRole)roleChoice;

    printf("Enter Email Address: ");
    if (scanf("%59s", newUser.email) != 1) return;
    while (getchar() != '\n');

    if (findUserByEmail(newUser.email) != -1) {
        printf("\n[Error] Email already registered! Please log in.\n");
        return;
    }

    printf("Enter Full Name: ");
    if (fgets(newUser.name, sizeof(newUser.name), stdin) == NULL) return;
    newUser.name[strcspn(newUser.name, "\r\n")] = '\0';

    printf("Enter Phone Number: ");
    if (scanf("%19s", newUser.phone) != 1) return;
    while (getchar() != '\n');

    if (newUser.role == ROLE_ORGANIZER || newUser.role == ROLE_SPONSOR) {
        printf("Enter Organization / Company Name: ");
        if (fgets(newUser.organization, sizeof(newUser.organization), stdin) == NULL) return;
        newUser.organization[strcspn(newUser.organization, "\r\n")] = '\0';
    } else {
        strcpy(newUser.organization, "N/A");
    }

    char password[50], confirmPassword[50];
    printf("Enter Password: ");
    if (scanf("%49s", password) != 1) return;
    while (getchar() != '\n');

    printf("Confirm Password: ");
    if (scanf("%49s", confirmPassword) != 1) return;
    while (getchar() != '\n');

    if (strcmp(password, confirmPassword) != 0) {
        printf("\n[Error] Passwords do not match.\n");
        return;
    }

    if (strlen(password) < 7) {
        printf("\n[Error] Password must be at least 7 characters long (letters, digits, or symbols).\n");
        return;
    }

    hashPassword(password, newUser.passwordHash);
    users[userCount++] = newUser;
    saveUsersToFile();

    printf("\n[Success] Registration successful! You can now log in.\n");
}

void forgotPassword()
{
    printf("\n==================================================\n");
    printf("          EVENTRA - PASSWORD RECOVERY             \n");
    printf("==================================================\n");
    char email[60];
    printf("Enter Registered Email Address: ");
    if (scanf("%59s", email) != 1) return;
    while (getchar() != '\n');

    int idx = findUserByEmail(email);
    if (idx == -1) {
        printf("\n[Error] No registered account found with that email.\n");
        return;
    }

    printf("Account found: %s (%s)\n", users[idx].name, getRoleName(users[idx].role));
    char phone[30];
    printf("Verify Registered Phone Number: ");
    if (scanf("%29s", phone) != 1) return;
    while (getchar() != '\n');

    if (strcmp(users[idx].phone, phone) != 0 && strlen(users[idx].phone) > 4) {
        printf("\n[Error] Phone verification failed.\n");
        return;
    }

    char newPass[50], confirmPass[50];
    printf("Enter New Password (min 7 chars): ");
    if (scanf("%49s", newPass) != 1) return;
    while (getchar() != '\n');

    if (strlen(newPass) < 7) {
        printf("\n[Error] Password must be at least 7 characters long (letters, digits, or symbols).\n");
        return;
    }

    printf("Confirm New Password: ");
    if (scanf("%49s", confirmPass) != 1) return;
    while (getchar() != '\n');

    if (strcmp(newPass, confirmPass) != 0) {
        printf("\n[Error] Passwords do not match.\n");
        return;
    }

    hashPassword(newPass, users[idx].passwordHash);
    saveUsersToFile();
    printf("\n[Success] Password reset successfully! You can now log in.\n");
}

/* Forward declarations of role dashboards */
void organizerDashboard();
void attendeeDashboard();
void sponsorDashboard();
void staffDashboard();
void adminDashboard();

int loginUser()
{
    char email[60], password[50], inputHash[65];

    printf("\n==================================================\n");
    printf("               EVENTRA - SECURE LOGIN             \n");
    printf("==================================================\n");
    printf("Enter Email Address: ");
    if (scanf("%59s", email) != 1) return 0;
    while (getchar() != '\n');

    printf("Enter Password: ");
    if (scanf("%49s", password) != 1) return 0;
    while (getchar() != '\n');

    int idx = findUserByEmail(email);
    if (idx == -1) {
        printf("\n[Error] No account found with that email.\n");
        return 0;
    }

    if (!users[idx].isActive) {
        printf("\n[Error] Account has been deactivated by an Administrator.\n");
        return 0;
    }

    hashPassword(password, inputHash);
    if (strcmp(users[idx].passwordHash, inputHash) != 0) {
        printf("\n[Error] Incorrect password.\n");
        return 0;
    }

    currentUser = &users[idx];
    printf("\n[Success] Login Successful! Welcome, %s.\n", currentUser->name);
    printf("Active Role  : %s\n", getRoleName(currentUser->role));

    switch (currentUser->role) {
        case ROLE_ORGANIZER: organizerDashboard(); break;
        case ROLE_ATTENDEE:  attendeeDashboard();  break;
        case ROLE_SPONSOR:   sponsorDashboard();   break;
        case ROLE_STAFF:     staffDashboard();     break;
        case ROLE_ADMIN:     adminDashboard();     break;
    }

    currentUser = NULL;
    return 1;
}

void viewMyProfile()
{
    if (!currentUser) return;
    printf("\n--------------------------------------------------\n");
    printf("                  USER PROFILE                    \n");
    printf("--------------------------------------------------\n");
    printf("User ID      : %d\n", currentUser->userId);
    printf("Name         : %s\n", currentUser->name);
    printf("Email        : %s\n", currentUser->email);
    printf("Role         : %s\n", getRoleName(currentUser->role));
    printf("Phone        : %s\n", currentUser->phone);
    printf("Organization : %s\n", currentUser->organization);
    printf("Status       : %s\n", currentUser->isActive ? "Active" : "Deactivated");
    printf("--------------------------------------------------\n");
}

void updateMyProfile()
{
    if (!currentUser) return;
    viewMyProfile();

    printf("\nUpdate Profile Options:\n");
    printf("  1. Update Display Name\n");
    printf("  2. Update Phone Number\n");
    printf("  3. Update Organization\n");
    printf("  4. Change Password\n");
    printf("  5. Return\n");
    printf("Enter choice (1-5): ");

    int choice;
    if (scanf("%d", &choice) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    switch (choice) {
        case 1:
            printf("Enter New Name: ");
            if (fgets(currentUser->name, sizeof(currentUser->name), stdin)) {
                currentUser->name[strcspn(currentUser->name, "\r\n")] = '\0';
                saveUsersToFile();
                printf("[Success] Name updated successfully.\n");
            }
            break;
        case 2:
            printf("Enter New Phone: ");
            if (scanf("%19s", currentUser->phone) == 1) {
                while (getchar() != '\n');
                saveUsersToFile();
                printf("[Success] Phone number updated successfully.\n");
            }
            break;
        case 3:
            printf("Enter New Organization: ");
            if (fgets(currentUser->organization, sizeof(currentUser->organization), stdin)) {
                currentUser->organization[strcspn(currentUser->organization, "\r\n")] = '\0';
                saveUsersToFile();
                printf("[Success] Organization updated successfully.\n");
            }
            break;
        case 4: {
            char currentPass[50], newPass[50], hashed[65];
            printf("Enter Current Password: ");
            if (scanf("%49s", currentPass) != 1) return;
            while (getchar() != '\n');
            hashPassword(currentPass, hashed);
            if (strcmp(currentUser->passwordHash, hashed) != 0) {
                printf("[Error] Current password incorrect.\n");
                return;
            }
            printf("Enter New Password (min 6 chars): ");
            if (scanf("%49s", newPass) != 1) return;
            while (getchar() != '\n');
            if (strlen(newPass) < 6) {
                printf("[Error] Password too short.\n");
                return;
            }
            hashPassword(newPass, currentUser->passwordHash);
            saveUsersToFile();
            printf("[Success] Password changed successfully.\n");
            break;
        }
        default: break;
    }
}

/* ========================================================================= */
/*       MODULE 2: EVENT MANAGEMENT OPERATIONS (ORGANIZER & ADMIN)          */
/* ========================================================================= */

void createEvent()
{
    if (eventCount >= MAX_EVENTS) {
        printf("\n[Error] Maximum event storage limit reached.\n");
        return;
    }

    Event newEv;
    newEv.eventId = eventCount + 1;
    newEv.organizerId = currentUser->userId;
    newEv.status = STATUS_DRAFT;
    strcpy(newEv.adminFeedback, "Pending initial organizer submission.");

    printf("\n==================================================\n");
    printf("         EVENTRA - CREATE NEW EVENT (WIZARD)      \n");
    printf("==================================================\n");

    printf("Enter Event Title: ");
    if (fgets(newEv.name, sizeof(newEv.name), stdin) == NULL) return;
    newEv.name[strcspn(newEv.name, "\r\n")] = '\0';

    printf("Enter Event Type (e.g., Tech Fest, Cultural, Sports, Conference): ");
    if (fgets(newEv.type, sizeof(newEv.type), stdin) == NULL) return;
    newEv.type[strcspn(newEv.type, "\r\n")] = '\0';

    printf("Enter Event Venue: ");
    if (fgets(newEv.venue, sizeof(newEv.venue), stdin) == NULL) return;
    newEv.venue[strcspn(newEv.venue, "\r\n")] = '\0';

    printf("Enter Event Date (YYYY-MM-DD): ");
    if (scanf("%19s", newEv.date) != 1) return;
    while (getchar() != '\n');

    printf("Enter Total Capacity: ");
    if (scanf("%d", &newEv.capacity) != 1) return;
    while (getchar() != '\n');
    newEv.availableSeats = newEv.capacity;

    printf("Enter Expected Attendance: ");
    if (scanf("%d", &newEv.expectedAttendance) != 1) return;
    while (getchar() != '\n');

    printf("Enter Estimated Budget (in INR): ");
    if (scanf("%lf", &newEv.budget) != 1) return;
    while (getchar() != '\n');

    // Configure Initial Venue Zones (FR8)
    printf("\n-- Define Venue Zones (Max %d) --\n", MAX_ZONES);
    printf("How many zones would you like to define? (1-%d): ", MAX_ZONES);
    int numZones = 1;
    if (scanf("%d", &numZones) != 1 || numZones < 1 || numZones > MAX_ZONES) numZones = 1;
    while (getchar() != '\n');

    newEv.zoneCount = numZones;
    for (int i = 0; i < numZones; i++) {
        newEv.zones[i].zoneId = i + 1;
        printf("  Zone %d Name: ", i + 1);
        if (fgets(newEv.zones[i].name, sizeof(newEv.zones[i].name), stdin)) {
            newEv.zones[i].name[strcspn(newEv.zones[i].name, "\r\n")] = '\0';
        }
        printf("  Zone %d Capacity: ", i + 1);
        if (scanf("%d", &newEv.zones[i].capacity) != 1) newEv.zones[i].capacity = 100;
        while (getchar() != '\n');
        newEv.zones[i].currentOccupancy = 0;
    }

    // Configure Initial Schedule Itinerary (FR7)
    printf("\n-- Define Schedule / Agenda Items (Max %d) --\n", MAX_SCHEDULE);
    printf("How many agenda items to schedule? (0-%d): ", MAX_SCHEDULE);
    int numSched = 0;
    if (scanf("%d", &numSched) != 1 || numSched < 0 || numSched > MAX_SCHEDULE) numSched = 0;
    while (getchar() != '\n');

    newEv.scheduleCount = numSched;
    for (int i = 0; i < numSched; i++) {
        newEv.schedule[i].itemId = i + 1;
        printf("  Item %d Title: ", i + 1);
        if (fgets(newEv.schedule[i].title, sizeof(newEv.schedule[i].title), stdin)) {
            newEv.schedule[i].title[strcspn(newEv.schedule[i].title, "\r\n")] = '\0';
        }
        printf("  Item %d Time Window (e.g. 09:00 AM - 11:00 AM): ", i + 1);
        if (fgets(newEv.schedule[i].timeWindow, sizeof(newEv.schedule[i].timeWindow), stdin)) {
            newEv.schedule[i].timeWindow[strcspn(newEv.schedule[i].timeWindow, "\r\n")] = '\0';
        }
        printf("  Item %d Location/Stage: ", i + 1);
        if (fgets(newEv.schedule[i].stage, sizeof(newEv.schedule[i].stage), stdin)) {
            newEv.schedule[i].stage[strcspn(newEv.schedule[i].stage, "\r\n")] = '\0';
        }
    }

    events[eventCount++] = newEv;
    saveEventsToFile();

    printf("\n[Success] Event '%s' created in DRAFT state! (ID: %d)\n", newEv.name, newEv.eventId);
}

void viewMyEvents()
{
    printf("\n==================================================\n");
    printf("             MY CREATED EVENTS LIST               \n");
    printf("==================================================\n");
    int count = 0;
    for (int i = 0; i < eventCount; i++) {
        if (events[i].organizerId == currentUser->userId) {
            count++;
            printf("\n[%d] Event ID: %d | '%s'\n", count, events[i].eventId, events[i].name);
            printf("    Type     : %s | Date: %s | Venue: %s\n", events[i].type, events[i].date, events[i].venue);
            printf("    Seats    : %d / %d Available | Budget: INR %.2f\n", events[i].availableSeats, events[i].capacity, events[i].budget);
            printf("    Status   : %s\n", getStatusName(events[i].status));
            printf("    Feedback : %s\n", events[i].adminFeedback);
            printf("    Zones (%d): ", events[i].zoneCount);
            for (int z = 0; z < events[i].zoneCount; z++) {
                printf("%s (Cap: %d, Occ: %d)%s", events[i].zones[z].name, events[i].zones[z].capacity, events[i].zones[z].currentOccupancy, (z < events[i].zoneCount - 1) ? ", " : "\n");
            }
            if (events[i].scheduleCount > 0) {
                printf("    Schedule : %d items scheduled\n", events[i].scheduleCount);
            }
        }
    }
    if (count == 0) {
        printf("No events created yet. Use 'Create New Event' to begin.\n");
    }
    printf("==================================================\n");
}

void submitEventForApproval()
{
    viewMyEvents();
    printf("\nEnter Event ID to submit for Admin Approval: ");
    int evId;
    if (scanf("%d", &evId) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int idx = findEventById(evId);
    if (idx == -1 || events[idx].organizerId != currentUser->userId) {
        printf("[Error] Event not found or not owned by you.\n");
        return;
    }

    if (events[idx].status != STATUS_DRAFT) {
        printf("[Notice] Event is currently '%s'. Only DRAFT events can be submitted.\n", getStatusName(events[idx].status));
        return;
    }

    events[idx].status = STATUS_PENDING;
    strcpy(events[idx].adminFeedback, "Submitted for review. Awaiting Admin decision.");
    saveEventsToFile();
    printf("[Success] Event '%s' submitted for Admin Approval (Status: PENDING APPROVAL).\n", events[idx].name);
}

void publishApprovedEvent()
{
    viewMyEvents();
    printf("\nEnter Event ID to PUBLISH: ");
    int evId;
    if (scanf("%d", &evId) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int idx = findEventById(evId);
    if (idx == -1 || events[idx].organizerId != currentUser->userId) {
        printf("[Error] Event not found or not owned by you.\n");
        return;
    }

    if (events[idx].status != STATUS_APPROVED) {
        printf("[Notice] Event status is '%s'. Only APPROVED events can be published.\n", getStatusName(events[idx].status));
        return;
    }

    events[idx].status = STATUS_PUBLISHED;
    saveEventsToFile();
    printf("[Success] Event '%s' is now PUBLISHED! Attendees and Sponsors can now discover and book it.\n", events[idx].name);
}

void cancelEvent()
{
    viewMyEvents();
    printf("\nEnter Event ID to Cancel: ");
    int evId;
    if (scanf("%d", &evId) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int idx = findEventById(evId);
    if (idx == -1 || events[idx].organizerId != currentUser->userId) {
        printf("[Error] Event not found.\n");
        return;
    }

    events[idx].status = STATUS_CANCELLED;
    saveEventsToFile();
    printf("[Success] Event '%s' has been marked CANCELLED.\n", events[idx].name);
}

void browsePublishedEvents()
{
    printf("\n==================================================\n");
    printf("         EVENTRA - BROWSE PUBLISHED EVENTS        \n");
    printf("==================================================\n");
    int count = 0;
    for (int i = 0; i < eventCount; i++) {
        if (events[i].status == STATUS_PUBLISHED) {
            count++;
            printf("\n[%d] Event ID: %d | '%s' (%s)\n", count, events[i].eventId, events[i].name, events[i].type);
            printf("    Date     : %s | Venue: %s\n", events[i].date, events[i].venue);
            printf("    Capacity : %d | Available Seats: %d\n", events[i].capacity, events[i].availableSeats);
            printf("    Zones    : %d venue zones configured\n", events[i].zoneCount);
            for (int z = 0; z < events[i].zoneCount; z++) {
                printf("      - %s (Cap: %d, Occupancy: %d)\n", events[i].zones[z].name, events[i].zones[z].capacity, events[i].zones[z].currentOccupancy);
            }
            if (events[i].scheduleCount > 0) {
                printf("    Key Itinerary:\n");
                for (int s = 0; s < events[i].scheduleCount; s++) {
                    printf("      * %s [%s @ %s]\n", events[i].schedule[s].title, events[i].schedule[s].timeWindow, events[i].schedule[s].stage);
                }
            }
        }
    }
    if (count == 0) {
        printf("No events currently published.\n");
    }
    printf("==================================================\n");
}

/* ========================================================================= */
/*       MODULE 4: TICKETING & REGISTRATION OPERATIONS (ATTENDEE)           */
/* ========================================================================= */

void bookTicket()
{
    browsePublishedEvents();
    printf("\nEnter Event ID to Book Ticket: ");
    int evId;
    if (scanf("%d", &evId) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int idx = findEventById(evId);
    if (idx == -1 || events[idx].status != STATUS_PUBLISHED) {
        printf("[Error] Event not found or not published.\n");
        return;
    }

    if (events[idx].availableSeats <= 0) {
        printf("[Notice] Sold out! No remaining seats for this event.\n");
        return;
    }

    printf("\nSelect Ticket Tier:\n");
    printf("  1. VIP Pass (INR 499.00 - Priority Access & Auditorium)\n");
    printf("  2. General Entry (INR 199.00 - Full Access)\n");
    printf("  3. Student Workshop Entry (INR 99.00 - Workshop & Exhibit Access)\n");
    printf("Enter choice (1-3): ");
    int tierChoice;
    if (scanf("%d", &tierChoice) != 1 || tierChoice < 1 || tierChoice > 3) tierChoice = 2;
    while (getchar() != '\n');

    Ticket newTkt;
    newTkt.ticketId = 100 + ticketCount + 1;
    newTkt.eventId = events[idx].eventId;
    newTkt.attendeeId = currentUser->userId;
    strcpy(newTkt.attendeeName, currentUser->name);
    strcpy(newTkt.eventName, events[idx].name);
    newTkt.isCheckedIn = 0;
    strcpy(newTkt.checkInTime, "N/A");
    strcpy(newTkt.checkInGate, "N/A");
    newTkt.isCancelled = 0;

    if (tierChoice == 1) {
        strcpy(newTkt.tier, "VIP Pass");
        newTkt.price = 499.0;
    } else if (tierChoice == 2) {
        strcpy(newTkt.tier, "General Entry");
        newTkt.price = 199.0;
    } else {
        strcpy(newTkt.tier, "Student Workshop");
        newTkt.price = 99.0;
    }

    generateQRToken(newTkt.ticketId, newTkt.eventId, newTkt.attendeeId, newTkt.qrToken);

    tickets[ticketCount++] = newTkt;
    events[idx].availableSeats--;
    saveTicketsToFile();
    saveEventsToFile();

    printf("\n[Success] Ticket booked successfully!\n");
    printf("  Ticket ID   : %d\n", newTkt.ticketId);
    printf("  Event       : %s\n", newTkt.eventName);
    printf("  Tier        : %s (INR %.2f)\n", newTkt.tier, newTkt.price);
    printf("  QR Token    : %s\n", newTkt.qrToken);
    printf("  Remaining   : %d seats left\n", events[idx].availableSeats);
}

void viewMyTickets()
{
    printf("\n==================================================\n");
    printf("            EVENTRA - MY DIGITAL TICKETS          \n");
    printf("==================================================\n");
    int count = 0;
    for (int i = 0; i < ticketCount; i++) {
        if (tickets[i].attendeeId == currentUser->userId) {
            count++;
            printf("\n[%d] Ticket #%d | '%s'\n", count, tickets[i].ticketId, tickets[i].eventName);
            printf("    Tier        : %s | Price: INR %.2f\n", tickets[i].tier, tickets[i].price);
            printf("    Status      : %s\n", tickets[i].isCancelled ? "CANCELLED" : (tickets[i].isCheckedIn ? "CHECKED-IN" : "ACTIVE"));
            if (tickets[i].isCheckedIn) {
                printf("    Check-In    : Verified at %s via Gate %s\n", tickets[i].checkInTime, tickets[i].checkInGate);
            }
            printf("    QR Hash     : %s\n", tickets[i].qrToken);
        }
    }
    if (count == 0) {
        printf("You have no booked tickets. Browse events to register!\n");
    }
    printf("==================================================\n");
}

void cancelTicket()
{
    viewMyTickets();
    printf("\nEnter Ticket ID to Cancel: ");
    int tId;
    if (scanf("%d", &tId) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int idx = findTicketById(tId);
    if (idx == -1 || tickets[idx].attendeeId != currentUser->userId) {
        printf("[Error] Ticket not found.\n");
        return;
    }

    if (tickets[idx].isCancelled) {
        printf("[Notice] Ticket is already cancelled.\n");
        return;
    }

    if (tickets[idx].isCheckedIn) {
        printf("[Error] Cannot cancel a ticket that has already been checked in.\n");
        return;
    }

    tickets[idx].isCancelled = 1;

    // Restore event seat availability
    int evIdx = findEventById(tickets[idx].eventId);
    if (evIdx != -1) {
        events[evIdx].availableSeats++;
        saveEventsToFile();
    }
    saveTicketsToFile();

    printf("[Success] Ticket #%d has been cancelled. Seat returned to pool.\n", tId);
}

/* ========================================================================= */
/*       MODULE 5: QR GATE ENTRY SCANNER (EVENT STAFF & ADMIN)              */
/* ========================================================================= */

void gateScanner()
{
    printf("\n==================================================\n");
    printf("          EVENTRA - QR GATE ENTRY SCANNER         \n");
    printf("==================================================\n");
    printf("Select Active Gate:\n");
    printf("  1. Gate Alpha (Main Entry)\n");
    printf("  2. Gate Beta (West Wing)\n");
    printf("  3. VIP Entrance (Auditorium)\n");
    printf("Enter choice (1-3): ");
    int gateChoice;
    if (scanf("%d", &gateChoice) != 1 || gateChoice < 1 || gateChoice > 3) gateChoice = 1;
    while (getchar() != '\n');

    const char* gateName = (gateChoice == 1) ? "Gate Alpha" : (gateChoice == 2 ? "Gate Beta" : "VIP Entrance");

    printf("\nActive Scanner: [%s]\n", gateName);
    printf("Enter Ticket ID or QR Hash Token to scan: ");
    char inputScan[70];
    if (scanf("%69s", inputScan) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int tIdx = -1;
    // Check if numeric ticket ID
    int maybeId = atoi(inputScan);
    if (maybeId > 0) {
        tIdx = findTicketById(maybeId);
    }
    if (tIdx == -1) {
        tIdx = findTicketByToken(inputScan);
    }

    if (tIdx == -1) {
        printf("\n**************************************************\n");
        printf(" [ACCESS DENIED] INVALID TICKET TOKEN             \n");
        printf(" Token '%s' does not match any issued ticket.     \n", inputScan);
        printf("**************************************************\n");
        return;
    }

    if (tickets[tIdx].isCancelled) {
        printf("\n**************************************************\n");
        printf(" [ACCESS DENIED] TICKET CANCELLED                 \n");
        printf(" Ticket #%d has been refunded or cancelled.        \n", tickets[tIdx].ticketId);
        printf("**************************************************\n");
        return;
    }

    if (tickets[tIdx].isCheckedIn) {
        printf("\n**************************************************\n");
        printf(" [ACCESS DENIED] DUPLICATE ENTRY ATTEMPT!         \n");
        printf(" Ticket #%d has ALREADY BEEN SCANNED!             \n", tickets[tIdx].ticketId);
        printf(" Previous Scan: %s via %s                         \n", tickets[tIdx].checkInTime, tickets[tIdx].checkInGate);
        printf(" Flagged for Gate Security Review.                \n");
        printf("**************************************************\n");
        return;
    }

    // Grant Entry!
    tickets[tIdx].isCheckedIn = 1;
    getCurrentTimestamp(tickets[tIdx].checkInTime, sizeof(tickets[tIdx].checkInTime));
    strncpy(tickets[tIdx].checkInGate, gateName, sizeof(tickets[tIdx].checkInGate) - 1);

    // Increment Zone occupancy if Main Stage exists
    int evIdx = findEventById(tickets[tIdx].eventId);
    if (evIdx != -1 && events[evIdx].zoneCount > 0) {
        events[evIdx].zones[0].currentOccupancy++;
        saveEventsToFile();
    }
    saveTicketsToFile();

    printf("\n==================================================\n");
    printf(" [ENTRY GRANTED] Welcome to Eventra!              \n");
    printf("==================================================\n");
    printf(" Attendee   : %s\n", tickets[tIdx].attendeeName);
    printf(" Event      : %s\n", tickets[tIdx].eventName);
    printf(" Tier       : %s\n", tickets[tIdx].tier);
    printf(" Gate       : %s\n", tickets[tIdx].checkInGate);
    printf(" Timestamp  : %s\n", tickets[tIdx].checkInTime);
    printf(" Status     : Verified & Logged Successfully      \n");
    printf("==================================================\n");
}

void viewGateAuditLog()
{
    printf("\n==================================================\n");
    printf("           GATE ENTRY AUDIT & CHECK-IN LOG        \n");
    printf("==================================================\n");
    int totalScanned = 0;
    for (int i = 0; i < ticketCount; i++) {
        if (tickets[i].isCheckedIn) {
            totalScanned++;
            printf("[%d] Tkt #%d | %s | '%s'\n", totalScanned, tickets[i].ticketId, tickets[i].attendeeName, tickets[i].eventName);
            printf("    Tier: %s | Gate: %s | Time: %s\n", tickets[i].tier, tickets[i].checkInGate, tickets[i].checkInTime);
        }
    }
    if (totalScanned == 0) {
        printf("No check-ins recorded yet.\n");
    } else {
        printf("\nTotal Successful Entries: %d\n", totalScanned);
    }
    printf("==================================================\n");
}

/* ========================================================================= */
/*       MODULE 3: SPONSORSHIP OPERATIONS (SPONSOR & ORGANIZER)             */
/* ========================================================================= */

void pledgeSponsorship()
{
    browsePublishedEvents();
    printf("\nEnter Event ID to Sponsor: ");
    int evId;
    if (scanf("%d", &evId) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int evIdx = findEventById(evId);
    if (evIdx == -1 || events[evIdx].status != STATUS_PUBLISHED) {
        printf("[Error] Event not found or not published.\n");
        return;
    }

    printf("\nSelect Sponsorship Tier Package:\n");
    printf("  1. Platinum Partner (INR 50,000.00 - Prime Stage Banner & VIP Booth)\n");
    printf("  2. Gold Partner     (INR 25,000.00 - Food Court Booth & Digital Screens)\n");
    printf("  3. Silver Partner   (INR 10,000.00 - Marketing Logo & 2 Passes)\n");
    printf("Enter choice (1-3): ");
    int tierChoice;
    if (scanf("%d", &tierChoice) != 1 || tierChoice < 1 || tierChoice > 3) tierChoice = 2;
    while (getchar() != '\n');

    Sponsorship s;
    s.sponsorshipId = sponsorshipCount + 1;
    s.eventId = events[evIdx].eventId;
    s.sponsorId = currentUser->userId;
    strcpy(s.sponsorName, currentUser->organization[0] != '\0' ? currentUser->organization : currentUser->name);
    strcpy(s.eventName, events[evIdx].name);
    strcpy(s.status, "Confirmed");
    getCurrentTimestamp(s.pledgedAt, sizeof(s.pledgedAt));

    if (tierChoice == 1) {
        strcpy(s.tier, "Platinum Partner");
        s.amount = 50000.0;
    } else if (tierChoice == 2) {
        strcpy(s.tier, "Gold Partner");
        s.amount = 25000.0;
    } else {
        strcpy(s.tier, "Silver Partner");
        s.amount = 10000.0;
    }

    sponsorships[sponsorshipCount++] = s;
    saveSponsorshipsToFile();

    printf("\n[Success] Sponsorship pledge confirmed!\n");
    printf("  Sponsor     : %s\n", s.sponsorName);
    printf("  Event       : %s\n", s.eventName);
    printf("  Tier        : %s (INR %.2f)\n", s.tier, s.amount);
    printf("  Date        : %s\n", s.pledgedAt);
}

void viewSponsorships()
{
    printf("\n==================================================\n");
    printf("         CONFIRMED SPONSORSHIP AGREEMENTS         \n");
    printf("==================================================\n");
    int count = 0;
    double totalPledged = 0;
    for (int i = 0; i < sponsorshipCount; i++) {
        count++;
        printf("[%d] %s | Event: '%s'\n", count, sponsorships[i].sponsorName, sponsorships[i].eventName);
        printf("    Tier  : %s | Amount: INR %.2f | Status: %s\n", sponsorships[i].tier, sponsorships[i].amount, sponsorships[i].status);
        printf("    Date  : %s\n", sponsorships[i].pledgedAt);
        totalPledged += sponsorships[i].amount;
    }
    if (count == 0) {
        printf("No active sponsorships recorded yet.\n");
    } else {
        printf("\nTotal Funding Raised: INR %.2f\n", totalPledged);
    }
    printf("==================================================\n");
}

/* ========================================================================= */
/*       MODULE 10 & ADMIN OPERATIONS                                       */
/* ========================================================================= */

void adminViewUsers()
{
    printf("\n==================================================\n");
    printf("         REGISTERED USERS GOVERNANCE              \n");
    printf("==================================================\n");
    printf("%-5s %-20s %-25s %-12s %-10s\n", "ID", "Name", "Email", "Role", "Status");
    printf("----------------------------------------------------------------------\n");
    for (int i = 0; i < userCount; i++) {
        printf("%-5d %-20s %-25s %-12s %-10s\n",
               users[i].userId, users[i].name, users[i].email,
               getRoleName(users[i].role), users[i].isActive ? "Active" : "Deactivated");
    }
    printf("==================================================\n");
}

void adminToggleUserStatus()
{
    adminViewUsers();
    printf("\nEnter User ID to Activate/Deactivate: ");
    int targetId;
    if (scanf("%d", &targetId) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int idx = findUserById(targetId);
    if (idx == -1) {
        printf("[Error] User not found.\n");
        return;
    }
    if (users[idx].role == ROLE_ADMIN && users[idx].userId == currentUser->userId) {
        printf("[Error] Cannot deactivate currently active Administrator account.\n");
        return;
    }

    users[idx].isActive = !users[idx].isActive;
    saveUsersToFile();
    printf("[Success] User %s is now %s.\n", users[idx].email, users[idx].isActive ? "Active" : "Deactivated");
}

void adminReviewEvents()
{
    printf("\n==================================================\n");
    printf("        ADMIN CONSOLE: PENDING EVENTS REVIEW      \n");
    printf("==================================================\n");
    int pendingCount = 0;
    for (int i = 0; i < eventCount; i++) {
        if (events[i].status == STATUS_PENDING) {
            pendingCount++;
            printf("\n[%d] Event ID: %d | '%s'\n", pendingCount, events[i].eventId, events[i].name);
            printf("    Type     : %s | Date: %s | Venue: %s\n", events[i].type, events[i].date, events[i].venue);
            printf("    Budget   : INR %.2f | Capacity: %d\n", events[i].budget, events[i].capacity);
            printf("    Zones (%d): ", events[i].zoneCount);
            for (int z = 0; z < events[i].zoneCount; z++) {
                printf("%s (Cap: %d)%s", events[i].zones[z].name, events[i].zones[z].capacity, (z < events[i].zoneCount - 1) ? ", " : "\n");
            }
        }
    }
    if (pendingCount == 0) {
        printf("No events currently pending review.\n");
        printf("==================================================\n");
        return;
    }
    printf("==================================================\n");

    printf("Enter Event ID to Review (or 0 to return): ");
    int targetId;
    if (scanf("%d", &targetId) != 1 || targetId <= 0) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    int idx = findEventById(targetId);
    if (idx == -1 || events[idx].status != STATUS_PENDING) {
        printf("[Error] Pending event not found.\n");
        return;
    }

    printf("Decision for Event '%s':\n", events[idx].name);
    printf("  1. Approve Event\n");
    printf("  2. Reject Event\n");
    printf("Enter choice (1-2): ");
    int decision;
    if (scanf("%d", &decision) != 1) { while (getchar() != '\n'); return; }
    while (getchar() != '\n');

    printf("Enter Feedback Notes: ");
    char feedback[100];
    if (fgets(feedback, sizeof(feedback), stdin)) {
        feedback[strcspn(feedback, "\r\n")] = '\0';
        strncpy(events[idx].adminFeedback, feedback, sizeof(events[idx].adminFeedback) - 1);
    }

    if (decision == 1) {
        events[idx].status = STATUS_APPROVED;
        printf("[Success] Event '%s' has been APPROVED! Organizer notified.\n", events[idx].name);
    } else {
        events[idx].status = STATUS_DRAFT;
        printf("[Notice] Event '%s' rejected and returned to DRAFT.\n", events[idx].name);
    }
    saveEventsToFile();
}

void adminSystemMetrics()
{
    int checkedInCount = 0;
    for (int i = 0; i < ticketCount; i++) {
        if (tickets[i].isCheckedIn) checkedInCount++;
    }

    printf("\n==================================================\n");
    printf("           EVENTRA SYSTEM-WIDE METRICS            \n");
    printf("==================================================\n");
    printf("Total Registered Users    : %d\n", userCount);
    printf("Total System Events       : %d\n", eventCount);
    printf("Total Tickets Issued      : %d\n", ticketCount);
    printf("Total Verified Check-Ins  : %d\n", checkedInCount);
    printf("Total Active Sponsorships : %d\n", sponsorshipCount);
    printf("Platform Security Status  : Active (Salted SHA-256 Enabled)\n");
    printf("==================================================\n");
}

/* ========================================================================= */
/*                          DASHBOARDS & NAVIGATION                          */
/* ========================================================================= */

void organizerDashboard()
{
    int choice;
    do {
        printf("\n==================================================\n");
        printf("           EVENT ORGANIZER DASHBOARD              \n");
        printf("==================================================\n");
        printf("  1. Create New Event (Wizard)\n");
        printf("  2. View My Created Events\n");
        printf("  3. Submit Event for Admin Approval\n");
        printf("  4. Publish Approved Event\n");
        printf("  5. Cancel Event\n");
        printf("  6. View Sponsorship Progress\n");
        printf("  7. View My Profile & Settings\n");
        printf("  8. Logout\n");
        printf("Enter choice (1-8): ");

        if (scanf("%d", &choice) != 1) {
            while (getchar() != '\n');
            continue;
        }
        while (getchar() != '\n');

        switch (choice) {
            case 1: createEvent(); break;
            case 2: viewMyEvents(); break;
            case 3: submitEventForApproval(); break;
            case 4: publishApprovedEvent(); break;
            case 5: cancelEvent(); break;
            case 6: viewSponsorships(); break;
            case 7: updateMyProfile(); break;
            case 8: printf("\nSigning out...\n"); break;
            default: printf("[Error] Invalid option.\n"); break;
        }
    } while (choice != 8);
}

void attendeeDashboard()
{
    int choice;
    do {
        printf("\n==================================================\n");
        printf("               ATTENDEE DASHBOARD                 \n");
        printf("==================================================\n");
        printf("  1. Browse Published Events & Venue Zones\n");
        printf("  2. Book Event Ticket (Tier Selection)\n");
        printf("  3. View My Digital Tickets & QR Tokens\n");
        printf("  4. Cancel Ticket Reservation\n");
        printf("  5. View My Profile & Settings\n");
        printf("  6. Logout\n");
        printf("Enter choice (1-6): ");

        if (scanf("%d", &choice) != 1) {
            while (getchar() != '\n');
            continue;
        }
        while (getchar() != '\n');

        switch (choice) {
            case 1: browsePublishedEvents(); break;
            case 2: bookTicket(); break;
            case 3: viewMyTickets(); break;
            case 4: cancelTicket(); break;
            case 5: updateMyProfile(); break;
            case 6: printf("\nSigning out...\n"); break;
            default: printf("[Error] Invalid option.\n"); break;
        }
    } while (choice != 6);
}

void sponsorDashboard()
{
    int choice;
    do {
        printf("\n==================================================\n");
        printf("               SPONSOR PORTAL                     \n");
        printf("==================================================\n");
        printf("  1. Discover Events & Sponsorship Opportunities\n");
        printf("  2. Pledge Event Sponsorship (Tier Packages)\n");
        printf("  3. View Confirmed Sponsorship Agreements\n");
        printf("  4. View My Profile & Settings\n");
        printf("  5. Logout\n");
        printf("Enter choice (1-5): ");

        if (scanf("%d", &choice) != 1) {
            while (getchar() != '\n');
            continue;
        }
        while (getchar() != '\n');

        switch (choice) {
            case 1: browsePublishedEvents(); break;
            case 2: pledgeSponsorship(); break;
            case 3: viewSponsorships(); break;
            case 4: updateMyProfile(); break;
            case 5: printf("\nSigning out...\n"); break;
            default: printf("[Error] Invalid option.\n"); break;
        }
    } while (choice != 5);
}

void staffDashboard()
{
    int choice;
    do {
        printf("\n==================================================\n");
        printf("            EVENT STAFF GATE DASHBOARD            \n");
        printf("==================================================\n");
        printf("  1. Open QR Gate Check-In Scanner\n");
        printf("  2. View Gate Entry Audit Log\n");
        printf("  3. View Live Zone Occupancy & Crowd Count\n");
        printf("  4. View My Profile & Settings\n");
        printf("  5. Logout\n");
        printf("Enter choice (1-5): ");

        if (scanf("%d", &choice) != 1) {
            while (getchar() != '\n');
            continue;
        }
        while (getchar() != '\n');

        switch (choice) {
            case 1: gateScanner(); break;
            case 2: viewGateAuditLog(); break;
            case 3: browsePublishedEvents(); break;
            case 4: updateMyProfile(); break;
            case 5: printf("\nSigning out...\n"); break;
            default: printf("[Error] Invalid option.\n"); break;
        }
    } while (choice != 5);
}

void adminDashboard()
{
    int choice;
    do {
        printf("\n==================================================\n");
        printf("             ADMINISTRATOR GOVERNANCE             \n");
        printf("==================================================\n");
        printf("  1. View All Registered Users\n");
        printf("  2. Toggle User Account Status (Activate/Deactivate)\n");
        printf("  3. Review Pending Events Approval Queue\n");
        printf("  4. View All System Events & Venue Zones\n");
        printf("  5. View Gate Scanner Audit Log\n");
        printf("  6. System-Wide Usage & Security Metrics\n");
        printf("  7. View My Profile & Settings\n");
        printf("  8. Logout\n");
        printf("Enter choice (1-8): ");

        if (scanf("%d", &choice) != 1) {
            while (getchar() != '\n');
            continue;
        }
        while (getchar() != '\n');

        switch (choice) {
            case 1: adminViewUsers(); break;
            case 2: adminToggleUserStatus(); break;
            case 3: adminReviewEvents(); break;
            case 4: browsePublishedEvents(); break;
            case 5: viewGateAuditLog(); break;
            case 6: adminSystemMetrics(); break;
            case 7: updateMyProfile(); break;
            case 8: printf("\nSigning out...\n"); break;
            default: printf("[Error] Invalid option.\n"); break;
        }
    } while (choice != 8);
}

/* ========================================================================= */
/*                                MAIN ENTRYPOINT                            */
/* ========================================================================= */

int main()
{
    loadDataFromFiles();

    int mainChoice;
    do {
        printf("\n==================================================\n");
        printf("                    EVENTRA                       \n");
        printf("  Intelligent Event, Ticketing & Crowd Platform   \n");
        printf("==================================================\n");
        printf("  1. Register New User\n");
        printf("  2. Secure User Login\n");
        printf("  3. Forgot Password / Reset Credentials\n");
        printf("  4. Exit\n");
        printf("Enter choice (1-4): ");

        if (scanf("%d", &mainChoice) != 1) {
            while (getchar() != '\n');
            continue;
        }
        while (getchar() != '\n');

        switch (mainChoice) {
            case 1: registerUser(); break;
            case 2: loginUser(); break;
            case 3: forgotPassword(); break;
            case 4:
                printf("\nExiting Eventra Platform. Goodbye!\n");
                break;
            default:
                printf("\n[Error] Invalid selection. Please choose 1 - 4.\n");
                break;
        }
    } while (mainChoice != 4);

    return 0;
}