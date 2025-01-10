cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(gst-rtsp-server REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} gst-rtsp-server::gstrtspserver-1.0 gst-rtsp-server::gstrtspclientsink)
