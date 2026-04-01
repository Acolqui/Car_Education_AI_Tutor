import UserInfo

def main():
    user = UserInfo.UserInfo("Alice", 30, "Intermediate")
    print(user)

    user.setUserInfo("Bob", 25, "Beginner")
    print(user.getUserInfo())





if __name__ == "__main__":
    main()
