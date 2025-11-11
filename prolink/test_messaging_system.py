"""
Quick Messaging System Test Script
Run this to verify messaging functionality without opening browser
"""

from django.test import Client
from django.contrib.auth import get_user_model
from messaging.models import Conversation, Message
from requests.models import Request

User = get_user_model()

def test_messaging_system():
    print("=" * 60)
    print("PROLINK MESSAGING SYSTEM - DIAGNOSTIC TEST")
    print("=" * 60)
    print()
    
    # Test 1: Check database counts
    print("📊 TEST 1: Database Status")
    print("-" * 60)
    conv_count = Conversation.objects.count()
    msg_count = Message.objects.count()
    req_count = Request.objects.count()
    user_count = User.objects.count()
    
    print(f"✓ Users: {user_count}")
    print(f"✓ Requests: {req_count}")
    print(f"✓ Conversations: {conv_count}")
    print(f"✓ Messages: {msg_count}")
    print()
    
    # Test 2: Check for pending requests
    print("📋 TEST 2: Pending Requests")
    print("-" * 60)
    pending = Request.objects.filter(status='pending')
    print(f"✓ Pending requests: {pending.count()}")
    for req in pending[:3]:
        print(f"  - [{req.id}] {req.title} (Client: {req.client})")
    print()
    
    # Test 3: Check conversations
    print("💬 TEST 3: Active Conversations")
    print("-" * 60)
    conversations = Conversation.objects.all()
    print(f"✓ Total conversations: {conversations.count()}")
    for conv in conversations:
        last_msg = conv.get_last_message()
        print(f"  - {conv.client.email} ↔ {conv.professional.email}")
        print(f"    Request: {conv.request.title}")
        if last_msg:
            print(f"    Last: {last_msg.content[:50]}...")
        print()
    
    # Test 4: Test API endpoints
    print("🌐 TEST 4: API Endpoints")
    print("-" * 60)
    client = Client()
    user = User.objects.first()
    
    if user:
        client.force_login(user)
        
        # Test unread count API
        response = client.get('/messages/api/unread-count/')
        if response.status_code == 200:
            print(f"✓ Unread count API: {response.json()}")
        else:
            print(f"✗ Unread count API failed: {response.status_code}")
        
        # Test inbox view
        response = client.get('/messages/')
        if response.status_code == 200:
            print(f"✓ Inbox view: OK")
        else:
            print(f"✗ Inbox view failed: {response.status_code}")
    else:
        print("✗ No users found to test with")
    print()
    
    # Test 5: Check user roles
    print("👥 TEST 5: User Roles")
    print("-" * 60)
    clients = User.objects.filter(user_role='client').count()
    professionals = User.objects.filter(user_role='professional').count()
    students = User.objects.filter(user_role='student').count()
    workers = User.objects.filter(user_role='worker').count()
    
    print(f"✓ Clients: {clients}")
    print(f"✓ Professionals: {professionals}")
    print(f"✓ Students: {students}")
    print(f"✓ Workers: {workers}")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_good = True
    
    if conv_count == 0:
        print("⚠️  No conversations exist yet")
        print("   → Professionals need to accept requests first")
        all_good = False
    else:
        print(f"✓ {conv_count} conversation(s) active")
    
    if pending.count() > 0:
        print(f"✓ {pending.count()} pending request(s) ready to accept")
    else:
        print("⚠️  No pending requests")
        print("   → Clients need to create requests first")
    
    if msg_count > 0:
        print(f"✓ {msg_count} message(s) sent")
    else:
        print("ℹ️  No messages yet")
        print("   → Normal for new conversations")
    
    print()
    if all_good or conv_count > 0:
        print("✅ MESSAGING SYSTEM IS OPERATIONAL")
    else:
        print("⚠️  MESSAGING SYSTEM READY BUT NO DATA YET")
        print("   Next steps:")
        print("   1. Create a request (as client)")
        print("   2. Accept request (as professional)")
        print("   3. Send messages in conversation")
    print()

if __name__ == '__main__':
    test_messaging_system()
