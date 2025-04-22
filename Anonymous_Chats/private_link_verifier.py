#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import logging
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("private_link_verifier.log")
    ]
)
logger = logging.getLogger("private_link_verifier")

# Database path
USER_DB_PATH = 'user_db.db'

def connect_database():
    """Connect to the user database."""
    try:
        conn = sqlite3.connect(USER_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None, None

def verify_private_link(link_text, user_id):
    """
    Verify a private link and establish connection if valid.
    
    Args:
        link_text: The private link text (starting with /92)
        user_id: The user ID of the person verifying the link
        
    Returns:
        A dictionary with status and message
    """
    try:
        # Remove the /92 prefix
        if link_text.startswith('/92'):
            link_text = link_text[3:]
        
        # Check if the link has enough characters
        if len(link_text) < 20:  # Arbitrary minimum length to contain all required parts
            return {
                "status": "error",
                "message": "⛔️Invalid private link format. Please check and try again."
            }
        
        # Extract parts from the link
        try:
            # A = 4 digits from 10th position (OTP)
            otp_from_link = link_text[6:10]
            
            # B = digits from 14th position before last 5 (USER_ID)
            peer_id_from_link = link_text[10:-5]
            
            logger.info(f"Extracted OTP: {otp_from_link}, Peer ID: {peer_id_from_link}")
        except IndexError:
            return {
                "status": "error",
                "message": "⛔️Invalid private link format. Please check and try again."
            }
        
        # Connect to database
        conn, cursor = connect_database()
        if not conn or not cursor:
            return {
                "status": "error",
                "message": "⛔️Database connection failed. Please try again later."
            }
        
        try:
            # Check if user is trying to connect to themselves
            if str(user_id) == str(peer_id_from_link):
                conn.close()
                return {
                    "status": "error",
                    "message": "⛔️You cannot connect to yourself. Please use a different private link."
                }
            
            # Verify the peer exists and has the matching OTP
            cursor.execute("SELECT OTP, STATUS FROM users WHERE USER_ID = ?", (peer_id_from_link,))
            peer_data = cursor.fetchone()
            
            if not peer_data:
                conn.close()
                return {
                    "status": "error",
                    "message": "⛔️Peer not found. Please check the private link and try again."
                }
            
            peer_otp, peer_status = peer_data
            
            # Verify OTP matches
            if not peer_otp or peer_otp != otp_from_link:
                conn.close()
                return {
                    "status": "error",
                    "message": "⛔️The private link may have expired or is incorrect."
                }
                
            # Always send a confirmation request regardless of peer's status
            # This ensures the receiver always gets a confirmation prompt
            conn.close()
            return {
                "status": "confirmation_needed",
                "message": "Confirmation needed from peer.",
                "peer_id": peer_id_from_link
            }
            
            # Check if the current user is already in a connection
            cursor.execute("SELECT STATUS, PEER_ID FROM users WHERE USER_ID = ?", (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                # Create user record if it doesn't exist
                cursor.execute("""
                INSERT INTO users (USER_ID, PEER_ID, TYPE, STATUS, TIMER, OTP)
                VALUES (?, ?, 'R48', 'PRIVATE', 5760, '')
                """, (user_id, peer_id_from_link))
            else:
                user_status, user_peer_id = user_data
                
                if user_peer_id:
                    conn.close()
                    return {
                        "status": "error",
                        "message": "You are already connected to someone. Please disconnect first."
                    }
                
                # Update user record to connect to peer
                cursor.execute("""
                UPDATE users 
                SET PEER_ID = ?, STATUS = 'PRIVATE', TIMER = 5760
                WHERE USER_ID = ?
                """, (peer_id_from_link, user_id))
            
            # Update peer record to connect to user
            cursor.execute("""
            UPDATE users 
            SET PEER_ID = ?, STATUS = 'PRIVATE', TIMER = 5760
            WHERE USER_ID = ?
            """, (user_id, peer_id_from_link))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Private connection established between user {user_id} and peer {peer_id_from_link}")
            
            return {
                "status": "success",
                "message": "Private Link Verified...\n\nYou are connected with your Peer privately.",
                "peer_id": peer_id_from_link
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error during private link verification: {e}")
            conn.close()
            return {
                "status": "error",
                "message": "⛔️Database error. Please try again later."
            }
            
    except Exception as e:
        logger.error(f"Error verifying private link: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": "⛔️An error occurred. Please try again later."
        }

# For testing purposes
if __name__ == "__main__":
    test_link = "/92106711426358442996730401"
    test_user_id = "123456789"
    print(verify_private_link(test_link, test_user_id))