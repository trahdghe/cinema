# logic.py

from database import (
    init_db,
    SEAT_PRICE,
    db_try_login                as try_login,
    db_register_user            as register_user,
    db_change_password          as change_password,
    db_get_users_list           as get_users_list,
    db_get_balance              as get_balance,
    db_get_halls_info           as get_halls_info,
    db_set_showtime             as set_showtime,
    db_get_hall_seats           as get_hall_seats,
    db_get_hall_seats_for_user  as get_hall_seats_for_user,
    db_reserve_seat             as reserve_seat,
    db_cancel_my_reservation    as cancel_my_reservation,
    db_admin_cancel_reservation as admin_cancel_reservation,
    db_get_my_bookings          as get_my_bookings,
    db_get_all_bookings         as get_all_bookings,
    db_get_statistics           as get_statistics,
    db_get_log_entries          as get_log_entries,
    db_get_refund_preview       as get_refund_preview,
)