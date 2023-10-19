cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

set(CMAKE_VERBOSE_MAKEFILE ON)

find_package(ads CONFIG REQUIRED)

add_executable(${PROJECT_NAME} example.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE ads::qt5advanceddocking)
