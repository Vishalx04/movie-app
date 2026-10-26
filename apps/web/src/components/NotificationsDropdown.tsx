"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Check } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { notificationApi } from "@/lib/api/notification";
import { Notification } from "@/types/notification";

export default function NotificationsDropdown({
  onClose,
}: {
  onClose?: () => void;
}) {
  const { access_token } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const handleMarkNotification = (
    e: React.MouseEvent,
    notificationId: number,
  ) => {
    if (!access_token) return;
    e.preventDefault();
    e.stopPropagation();
    notificationApi.markAsRead(notificationId, access_token);
  };

  useEffect(() => {
    if (!access_token) return;

    notificationApi
      .getNotifications(access_token, true)
      .then((data) => setNotifications(data))
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  }, [access_token]);

  return (
    <div className="absolute right-0 top-full mt-2 w-80 rounded-xl bg-panel border border-ash/15 shadow-card p-3 z-50 animate-fade-in">
      <p className="font-sans text-[11px] uppercase tracking-wider text-ash mb-2 px-2">
        Notifications
      </p>

      {isLoading ? (
        <p className="font-sans text-xs text-ash px-2 py-4 text-center">
          Loading...
        </p>
      ) : notifications.length === 0 ? (
        <p className="font-sans text-xs text-ash px-2 py-4 text-center">
          No notifications yet
        </p>
      ) : (
        <div className="max-h-64 overflow-y-auto space-y-1">
          {notifications.map((n) => (
            <Link
              key={n.id}
              href={`/movies/${n.movie_id}`}
              onClick={onClose}
              className={`block p-2.5 rounded-lg text-xs font-sans transition-colors ${n.is_read
                ? "text-ash hover:bg-ink/5"
                : "text-ink font-medium bg-ash/5 hover:bg-ink/5"
                }`}
            >
              <div className="flex items-center justify-between gap-2.5">
                <span className="flex-1">{n.message}</span>
                {!n.is_read && (
                  <button
                    type="button"
                    onClick={(e) => handleMarkNotification(e, n.id)}
                    title="Mark as read"
                    className="shrink-0 p-1 rounded hover:bg-ink/5 transition-colors cursor-pointer"
                  >
                    <Check className="h-4 w-4 text-data" />
                  </button>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
