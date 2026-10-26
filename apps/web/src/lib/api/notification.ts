import { Notification } from "@/types/notification";
import { apifetch } from "../api-client";

export const notificationApi = {
  getNotifications: (accessToken: string, unreadOnly: boolean = false) => {
    const query = unreadOnly ? "?unread_only=true" : "";
    return apifetch<Notification[]>(
      `/notifications/me${query}`,
      {
        method: "GET",
      },
      accessToken,
    );
  },
  markAsRead: (notificationId: number, accessToken: string) => {
    return apifetch<Notification>(
      `/notifications/${notificationId}/read`,
      {
        method: "PATCH",
      },
      accessToken,
    );
  },
};
