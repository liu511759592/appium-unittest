import random
import time
from library.core.TestCase import TestCase
from library.core.utils.applicationcache import current_mobile, switch_to_mobile
from library.core.utils.testcasefilter import tags
from pages import *

REQUIRED_MOBILES = {
    # 'Android-移动': 'single_mobile',
    'Android-移动': 'M960BDQN229CH',
    'Android-移动-联通': 'mobile_and_union',
    'Android-移动-电信': '',
    'Android-移动-移动': 'double_mobile',
    'Android-XX-XX': 'others_double',
}


class Preconditions(object):
    """前置条件"""

    @staticmethod
    def select_mobile(category, reset=False):
        """选择手机"""
        client = switch_to_mobile(REQUIRED_MOBILES[category])
        client.connect_mobile()
        if reset:
            current_mobile().reset_app()
        return client

    @staticmethod
    def make_already_in_one_key_login_page():
        """已经进入一键登录页"""
        # 如果当前页面已经是一键登录页，不做任何操作
        one_key = OneKeyLoginPage()
        if one_key.is_on_this_page():
            return

        # 如果当前页不是引导页第一页，重新启动app
        guide_page = GuidePage()
        if not guide_page.is_on_the_first_guide_page():
            # current_mobile().launch_app()
            current_mobile().reset_app()
            guide_page.wait_for_page_load(20)

        # 跳过引导页
        guide_page.wait_for_page_load(30)
        guide_page.swipe_to_the_second_banner()
        guide_page.swipe_to_the_third_banner()
        guide_page.click_start_the_experience()

        # 点击权限列表页面的确定按钮
        permission_list = PermissionListPage()
        permission_list.click_submit_button()
        one_key.wait_for_page_load(30)

    @staticmethod
    def login_by_one_key_login():
        """
        从一键登录页面登录
        :return:
        """
        # 等待号码加载完成后，点击一键登录
        one_key = OneKeyLoginPage()
        one_key.wait_for_tell_number_load(60)
        one_key.click_one_key_login()
        one_key.click_read_agreement_detail()

        # 同意协议
        agreement = AgreementDetailPage()
        agreement.click_agree_button()

        # 等待消息页
        message_page = MessagePage()
        message_page.wait_for_page_load(60)

    @staticmethod
    def make_already_in_message_page(reset=False):
        """确保应用在消息页面"""
        Preconditions.select_mobile('Android-移动', reset)
        # 如果在消息页，不做任何操作
        mess = MessagePage()
        if mess.is_on_this_page():
            return
        # 进入一键登录页
        Preconditions.make_already_in_one_key_login_page()
        #  从一键登录页面登录
        Preconditions.login_by_one_key_login()

    @staticmethod
    def enter_private_chat_page(reset=False):
        """进入单聊会话页面"""
        # 登录进入消息页面
        Preconditions.make_already_in_message_page(reset)
        mess = MessagePage()
        # 点击‘通讯录’
        mess.open_contacts_page()
        contacts = ContactsPage()
        contacts.wait_for_page_load()
        names = contacts.get_contacts_name()
        chat = SingleChatPage()
        cdp = ContactDetailsPage()
        # 不存在联系则创建联系人
        if not names:
            contacts.click_add()
            ccp = CreateContactPage()
            ccp.wait_for_page_load()
            name = "atest" + str(random.randint(100, 999))
            number = "147752" + str(time.time())[-5:]
            ccp.create_contact(name, number)
        contacts.select_people_by_name(names[0])
        cdp.wait_for_page_load()
        # 点击消息进入单聊会话页面
        cdp.click_message_icon()
        # 如果弹框用户须知则点击处理
        flag = chat.is_exist_dialog()
        if flag:
            chat.click_i_have_read()
        chat.wait_for_page_load()


class MsgPrivateChatFileLocationTest(TestCase):
    """消息->单聊文件,位置 模块"""

    # @classmethod
    # def setUpClass(cls):
    #     # 进入单聊会话页面
    #     Preconditions.enter_private_chat_page()

    def default_setUp(self):
        """确保每个用例运行前在单聊会话页面"""
        chat = SingleChatPage()
        if chat.is_on_this_page():
            return
        else:
            current_mobile().disconnect_mobile()
            Preconditions.enter_private_chat_page()

    @staticmethod
    def public_send_file(file_type):
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击本地文件
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_local_file()
        # 3、选择任意文件，点击发送按钮
        local_file = ChatSelectLocalFilePage()
        # 没有预置文件，则上传
        flag = local_file.push_preset_file()
        if flag:
            local_file.click_back()
            csf.click_local_file()
        # 进入预置文件目录，选择文件发送
        local_file.click_preset_file_dir()
        file = local_file.select_file(file_type)
        if file:
            local_file.click_send()
        else:
            local_file.click_back()
            local_file.click_back()
            csf.click_back()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0001(self):
        """单聊会话页面，不勾选本地文件内文件点击发送按钮"""
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击本地文件
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_local_file()
        # 3、不选择文件，直接点击发送按钮
        local_file = ChatSelectLocalFilePage()
        flag = local_file.send_btn_is_enabled()
        self.assertFalse(flag)
        # 返回聊天会话页面
        local_file.click_back()
        csf.click_back()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0002(self):
        """ 单聊会话页面，勾选本地文件内任意文件点击发送按钮"""
        self.public_send_file('.txt')

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0003(self):
        """单聊会话页面，不勾选本地视频文件内视频点击发送按钮"""
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击视频
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_video()
        # 3、不选择视频，直接点击发送按钮
        local_file = ChatSelectLocalFilePage()
        flag = local_file.send_btn_is_enabled()
        self.assertFalse(flag)
        # 返回聊天会话页面
        local_file.click_back()
        csf.click_back()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0004(self):
        """单聊会话页面，勾选本地视频文件内任意视频点击发送按钮"""
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击视频
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_video()
        # 3、选择视频，直接点击发送按钮
        local_file = ChatSelectLocalFilePage()
        el = local_file.select_file2("视频")
        if el:
            local_file.click_send()
            chat.wait_for_page_load()
        else:
            local_file.click_back()
            csf.click_back()
            chat.wait_for_page_load()
            raise AssertionError("There is no video")

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0005(self):
        """单聊会话页面，不勾选本地照片文件内照片点击发送按钮"""
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击照片
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_pic()
        # 3、不选择照片，直接点击发送按钮
        local_file = ChatSelectLocalFilePage()
        flag = local_file.send_btn_is_enabled()
        self.assertFalse(flag)
        # 返回聊天会话页面
        local_file.click_back()
        csf.click_back()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0006(self):
        """单聊会话页面，勾选本地照片文件内任意照片点击发送按钮"""
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击照片
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_pic()
        # 3、选择照片，直接点击发送按钮
        local_file = ChatSelectLocalFilePage()
        el = local_file.select_file2("照片")
        if el:
            local_file.click_send()
            chat.wait_for_page_load()
        else:
            local_file.click_back()
            csf.click_back()
            chat.wait_for_page_load()
            raise AssertionError("There is no pic")

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0007(self):
        """单聊会话页面，不勾选本地音乐文件内音乐点击发送按钮"""
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击音乐
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_music()
        # 3、不选择音乐，直接点击发送按钮
        local_file = ChatSelectLocalFilePage()
        flag = local_file.send_btn_is_enabled()
        self.assertFalse(flag)
        # 返回聊天会话页面
        local_file.click_back()
        csf.click_back()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0008(self):
        """单聊会话页面，勾选本地音乐文件内任意音乐点击发送按钮"""
        # 1、在当前聊天会话页面，点击更多富媒体的文件按钮
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        # 2、点击音乐
        more_page = ChatMorePage()
        more_page.click_file()
        csf = ChatSelectFilePage()
        csf.wait_for_page_load()
        csf.click_music()
        # 3、选择音乐，直接点击发送按钮
        local_file = ChatSelectLocalFilePage()
        el = local_file.select_file2("音乐")
        if el:
            local_file.click_send()
            chat.wait_for_page_load()
        else:
            local_file.click_back()
            csf.click_back()
            chat.wait_for_page_load()
            raise AssertionError("There is no music")

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0019(self):
        """单聊设置-查找聊天内容-文件页面，长按文件进行删除"""
        self.public_send_file('.xlsx')
        chat = SingleChatPage()
        # 点击设置
        chat.click_setting()
        set_page = SingleChatSetPage()
        # 点击查找聊天内容
        set_page.search_chat_record()
        search = FindChatRecordPage()
        # 点击文件
        search.click_file()
        chat_file = ChatFilePage()
        chat_file.wait_for_page_load()
        chat_file.delete_file(".xlsx")
        # 返回聊天会话页面
        chat_file.click_back()
        search.click_back()
        set_page.click_back()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0040(self):
        """单聊天会话页面，长按文件进行删除"""
        # 预置数据，发送文件
        self.public_send_file('.xlsx')
        chat = SingleChatPage()
        # 长按文件删除
        chat.delete_mess(".xlsx")
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0041(self):
        """单聊天会话页面，长按自己发送的文件，十分钟内撤回"""
        # 预置数据，发送文件
        self.public_send_file('.xlsx')
        chat = SingleChatPage()
        # 长按文件撤回消息
        chat.recall_mess(".xlsx")
        if chat.is_text_present("我知道了"):
            chat.click_i_know()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'SLOW')
    def test_msg_private_chat_file_location_0042(self):
        """单聊天会话页面，长按自己发送的文件，超过十分钟撤回"""
        self.public_send_file('.xlsx')
        chat = SingleChatPage()
        # 超过十分钟,长按自己发送的文件撤回，没有撤回菜单按钮
        for i in range(122):
            time.sleep(2)
            text = chat.driver.page_source
            del text
            time.sleep(3)
            tmp = chat.driver.current_activity
            del tmp
            print(i)
        chat.press_mess(".xlsx")
        flag = chat.is_text_present("撤回")
        self.assertFalse(flag)
        # 删除文件，关闭弹框菜单
        chat.click_delete()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0043(self):
        """单聊天会话页面，点击位置，再返回到会话页面"""
        # 1、在当前会话窗口点击位置
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        more_page = ChatMorePage()
        more_page.click_location()
        location_page = ChatLocationPage()
        location_page.wait_for_page_load()
        # 2、点击左上角的返回按钮
        location_page.click_back()
        chat.click_more()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0044(self):
        """单聊天会话页面，点击位置，默认当前位置直接发送"""
        # 1、在当前会话窗口点击位置
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        more_page = ChatMorePage()
        more_page.click_location()
        location_page = ChatLocationPage()
        location_page.wait_for_page_load()
        # 2、点击右上角的发送按钮
        location_page.click_send()
        chat.wait_for_page_load()
        chat.click_more()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0045(self):
        """单聊天会话页面，点击位置，选择500米内的其他位置发送"""
        # 1、在当前会话窗口点击位置
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        more_page = ChatMorePage()
        more_page.click_location()
        location_page = ChatLocationPage()
        location_page.wait_for_page_load()
        # 2、滑动500米内的位置列表，选择其他位置
        location_page.select_other_item()
        # 3、点击右上角的发送按钮
        location_page.click_send()
        chat.wait_for_page_load()
        chat.click_more()
        chat.wait_for_page_load()

    @tags('ALL', 'SMOKE', 'CMCC')
    def test_msg_private_chat_file_location_0046(self):
        """单聊天会话页面，点击位置，选择500米内的其他位置后返回到会话窗口"""
        # 1、在当前会话窗口点击位置
        chat = SingleChatPage()
        chat.wait_for_page_load()
        chat.click_more()
        more_page = ChatMorePage()
        more_page.click_location()
        location_page = ChatLocationPage()
        location_page.wait_for_page_load()
        # 2、滑动500米内的位置列表，选择其他位置
        location_page.select_other_item()
        # 3、点击左上角的返回按钮
        location_page.click_back()
        chat.wait_for_page_load()
        chat.click_more()
        chat.wait_for_page_load()
