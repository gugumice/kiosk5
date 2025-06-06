#!/usr/bin/env python3
''' A module for utility classes and functions. '''

from enum import Enum, auto
from queue import Queue
import logging
class TicketPurpose(Enum):
    '''Enum class to represent the purpose of the ticket.'''
    REP = auto() # Report ticket
    BC = auto()  # Barcode reader ticket
    PRN = auto() # Printer ticket
    NET = auto() # Network ticket
    SYS = auto() # System ticket

class Ticket(object):
    def __init__(self, ticket_type = TicketPurpose, ticket_value: str= None):
        self.ticket_type = ticket_type
        self.ticket_value = ticket_value

def send_ticket(ticket_value:str = None, ticket_type:Ticket = TicketPurpose.SYS, queue_tx:Queue = None):
    """
    Function to send a ticket to the service thread.
    :param value: Value of the ticket
    :param : Type of the ticket (TicketPurpose)
    """
    ticket = Ticket(ticket_type=TicketPurpose.BC, ticket_value=ticket_value)
    queue_tx.put(ticket)
    logging.info(f"Ticket sent: {ticket.ticket_value} of type {ticket.ticket_type}")